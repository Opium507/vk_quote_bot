from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

from app.bot.author_resolver import AuthorResolver
from app.bot.callbacks import parse_callback_payload
from app.bot.messages import build_help_text, build_render_error_text
from app.bot.peer import is_private_peer
from app.bot.quote_service import QuoteService
from app.bot.state import UserStateStore
from app.bot.style_service import StyleService
from app.bot.vk_client import VkBotClient
from app.bot.user_manager import UserManager
from app.config import get_settings
from app.domain.models import RenderMode
from app.render.single_renderer import render_single_quote
from app.render.thread_renderer import render_thread_quote
from app.logger import logger

import requests
import traceback


def safe_send_rendered_photo(
    vk_client: VkBotClient,
    peer_id: int,
    user_id: int,                 # <-- добавляем
    render_func,
    request,
    user_manager: UserManager,    # <-- добавляем
) -> None:
    try:
        image_path = render_func(request)
        vk_client.send_photo(
            peer_id=peer_id,
            image_path=image_path,
        )
        # Увеличиваем счётчик только после успешной отправки
        user_manager.increment_render_count(user_id)

    except Exception:
        traceback.print_exc()
        logger.error("Ошибка при рендеринге или отправке фото", exc_info=True)
        vk_client.send_text(
            peer_id=peer_id,
            message=build_render_error_text(),
        )


def main() -> None:
    settings = get_settings()

    vk_client = VkBotClient(
        token=settings.vk_group_token,
        group_id=settings.vk_group_id,
    )
    longpoll = VkBotLongPoll(vk_client.session, settings.vk_group_id)

    state_store = UserStateStore(default_style=settings.default_style)
    style_service = StyleService(state_store=state_store)
    author_resolver = AuthorResolver(vk_client=vk_client)
    quote_service = QuoteService(
        state_store=state_store,
        settings=settings,
        author_resolver=author_resolver,
    )
    user_manager = UserManager(superadmin_id=settings.superadmin_id)

    logger.info("Bot started...")
    logger.info(f"Superadmin ID: {settings.superadmin_id}")

    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                handle_message_new(event, vk_client, style_service, quote_service, user_manager, author_resolver)
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                handle_message_event(event, vk_client, style_service)
                
        except Exception as e:
            logger.error("Необработанная ошибка в longpoll", exc_info=True)

def handle_message_new(
    event,
    vk_client: VkBotClient,
    style_service: StyleService,
    quote_service: QuoteService,
    user_manager: UserManager,
    author_resolver: AuthorResolver,
) -> None:
    message = event.object["message"]
    text = (message.get("text") or "").strip().lower()
    peer_id = message["peer_id"]
    from_id = message["from_id"]

    if not is_private_peer(peer_id):
        return

    # --- Команды суперадмина (до проверки прав) ---
    if from_id == user_manager.superadmin_id:
        # !добавить
        if text == "!добавить":
            fwd_messages = message.get("fwd_messages") or []
            if not fwd_messages:
                vk_client.send_text(peer_id=peer_id, message="Перешлите сообщение пользователя, которого нужно добавить.")
                return

            target_id = fwd_messages[0].get("from_id")
            if not target_id:
                vk_client.send_text(peer_id=peer_id, message="Не удалось определить пользователя в пересланном сообщении.")
                return

            # Получаем имя пользователя через API
            try:
                user_info = vk_client.api.users.get(user_ids=target_id, fields="first_name,last_name")
                if user_info:
                    name = f"{user_info[0].get('first_name', '')} {user_info[0].get('last_name', '')}".strip()
                else:
                    name = f"User {target_id}"
            except Exception:
                name = f"User {target_id}"

            if user_manager.add_user(target_id, name):
                vk_client.send_text(peer_id=peer_id, message=f"✅ Пользователь {name} добавлен в список.")
            else:
                vk_client.send_text(peer_id=peer_id, message="⚠️ Пользователь уже есть в списке.")
            return

        # !удалить <id или упоминание>
        if text.startswith("!удалить"):
            parts = text.split()
            if len(parts) < 2:
                vk_client.send_text(peer_id=peer_id, message="Укажите ID пользователя или перешлите его сообщение.\nПример: !удалить 123456789")
                return

            target_str = parts[1]
            try:
                target_id = int(target_str)
            except ValueError:
                # пробуем извлечь из упоминания [id123|Имя]
                import re
                match = re.search(r"\[id(\d+)\|", target_str)
                if match:
                    target_id = int(match.group(1))
                else:
                    vk_client.send_text(peer_id=peer_id, message="Неверный формат. Укажите числовой ID.")
                    return

            if user_manager.remove_user(target_id):
                vk_client.send_text(peer_id=peer_id, message=f"✅ Пользователь {target_id} удалён из списка.")
            else:
                vk_client.send_text(peer_id=peer_id, message="⚠️ Пользователь не найден в списке.")
            return

        # !ц список
    if text == "!ц список":
        users = user_manager.list_users()
        total_renders = user_manager.get_total_renders()
        superadmin_count = user_manager.get_superadmin_render_count()

        # Получаем имя суперадмина через VK API
        try:
            superadmin_info = vk_client.api.users.get(
                user_ids=user_manager.superadmin_id,
                fields="first_name,last_name"
            )
            if superadmin_info:
                first = superadmin_info[0].get('first_name', '')
                last = superadmin_info[0].get('last_name', '')
                superadmin_name = f"{first} {last}".strip()
            else:
                superadmin_name = f"Суперадмин (id{user_manager.superadmin_id})"
        except Exception:
            superadmin_name = f"Суперадмин (id{user_manager.superadmin_id})"

        lines = ["📋 Добавлены к цитированию:"]
        for u in users:
            lines.append(f"  ■ [vk.ru/id{u['id']}|{u['name']}] {u.get('render_count', 0)}")

        lines.append(f"\n👑 Суперадмин:\n  ■ [vk.ru/id{user_manager.superadmin_id}|{superadmin_name}] {superadmin_count}")
        lines.append(f"\n📊 Всего рендеров: {total_renders}")
        vk_client.send_text(peer_id=peer_id, message="\n".join(lines))
        return
                
    # --- Проверка доступа для всех остальных команд ---
    if not user_manager.is_allowed(from_id):
        vk_client.send_text(peer_id=peer_id, message="У вас нет доступа к боту. Обратитесь к администратору.")
        return

    # --- Обычные команды ---
    if text in {"!help", "!помощь", "!команды"}:
        vk_client.send_text(
            peer_id=peer_id,
            message=build_help_text(),
        )
        return

    if text in {"!стиль", "!style", "!style"}:
        response_text, keyboard = style_service.build_style_menu_response()
        vk_client.send_text(
            peer_id=peer_id,
            message=response_text,
            keyboard=keyboard,
        )
        return

    if text == "!цитата":
        request, error_text = quote_service.build_single_render_request(
            user_id=from_id,
            message=message,
        )

        if error_text:
            vk_client.send_text(
                peer_id=peer_id,
                message=error_text,
            )
            return

        if request is None or request.mode != RenderMode.SINGLE:
            vk_client.send_text(
                peer_id=peer_id,
                message=build_render_error_text(),
            )
            return

        safe_send_rendered_photo(
            vk_client=vk_client,
            peer_id=peer_id,
            user_id=from_id,
            render_func=render_single_quote,
            request=request,
            user_manager=user_manager,
        )
        return

    if text == "!цитата все":
        request, error_text = quote_service.build_thread_render_request(
            user_id=from_id,
            message=message,
        )

        if error_text:
            vk_client.send_text(
                peer_id=peer_id,
                message=error_text,
            )
            return

        if request is None or request.mode != RenderMode.THREAD:
            vk_client.send_text(
                peer_id=peer_id,
                message=build_render_error_text(),
            )
            return

        safe_send_rendered_photo(
            vk_client=vk_client,
            peer_id=peer_id,
            user_id=from_id,
            render_func=render_single_quote,
            request=request,
            user_manager=user_manager,
        )
        return


def handle_message_event(event, vk_client: VkBotClient, style_service: StyleService) -> None:
    payload = parse_callback_payload(event.object.get("payload"))
    if payload is None:
        return

    peer_id = event.object["peer_id"]
    user_id = event.object["user_id"]
    event_id = event.object["event_id"]
    conversation_message_id = event.object["conversation_message_id"]

    if not is_private_peer(peer_id):
        return

    if payload.command == "style_menu":
        response_text, keyboard = style_service.build_style_menu_response(
            page=payload.page or 1,
        )

        vk_client.edit_text(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            message=response_text,
            keyboard=keyboard,
        )
        vk_client.answer_callback(
            event_id=event_id,
            user_id=user_id,
            peer_id=peer_id,
            text="Открыто меню стилей",
        )
        return

    if payload.command == "style_select":
        response_text, keyboard, snackbar_text = style_service.select_style_for_user(
            user_id=user_id,
            style_key=payload.style_key,
            page=payload.page or 1,
        )

        vk_client.edit_text(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            message=response_text,
            keyboard=keyboard,
        )
        vk_client.answer_callback(
            event_id=event_id,
            user_id=user_id,
            peer_id=peer_id,
            text=snackbar_text,
        )
        return

    if payload.command == "style_page_prev":
        response_text, keyboard, snackbar_text = style_service.paginate_styles(
            current_page=payload.page or 1,
            direction="prev",
        )

        vk_client.edit_text(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            message=response_text,
            keyboard=keyboard,
        )
        vk_client.answer_callback(
            event_id=event_id,
            user_id=user_id,
            peer_id=peer_id,
            text=snackbar_text,
        )
        return

    if payload.command == "style_page_next":
        response_text, keyboard, snackbar_text = style_service.paginate_styles(
            current_page=payload.page or 1,
            direction="next",
        )

        vk_client.edit_text(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            message=response_text,
            keyboard=keyboard,
        )
        vk_client.answer_callback(
            event_id=event_id,
            user_id=user_id,
            peer_id=peer_id,
            text=snackbar_text,
        )
        return

    if payload.command == "style_stub":
        response_text, keyboard, snackbar_text = style_service.get_stub_response(
            page=payload.page or 1,
        )

        vk_client.edit_text(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            message=response_text,
            keyboard=keyboard,
        )
        vk_client.answer_callback(
            event_id=event_id,
            user_id=user_id,
            peer_id=peer_id,
            text=snackbar_text,
        )
        return


if __name__ == "__main__":
    main()