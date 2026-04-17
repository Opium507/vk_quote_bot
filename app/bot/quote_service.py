from app.bot.author_resolver import AuthorResolver
from app.bot.forward_parser import extract_forward_list, extract_single_forward
from app.bot.messages import (
    build_empty_forward_text,
    build_missing_forward_text,
    build_too_many_forwards_text,
)
from app.bot.state import UserStateStore
from app.config import Settings
from app.domain.models import QuoteRenderRequest, RenderMode
from app.render.theme_loader import get_theme


class QuoteService:
    def __init__(
        self,
        state_store: UserStateStore,
        settings: Settings,
        author_resolver: AuthorResolver,
    ) -> None:
        self._state_store = state_store
        self._settings = settings
        self._author_resolver = author_resolver

    def build_single_render_request(
        self,
        user_id: int,
        message: dict,
    ) -> tuple[QuoteRenderRequest | None, str | None]:
        forwarded = extract_single_forward(message)
        if forwarded is None:
            return None, build_missing_forward_text()

        forwarded = self._author_resolver.enrich_message(forwarded)

        theme = get_theme(self._state_store.get_style(user_id))
        request = QuoteRenderRequest(
            mode=RenderMode.SINGLE,
            theme=theme,
            messages=[forwarded],
        )
        return request, None

    def build_thread_render_request(
        self,
        user_id: int,
        message: dict,
    ) -> tuple[QuoteRenderRequest | None, str | None]:
        raw_forwards = message.get("fwd_messages") or []
        if not raw_forwards:
            return None, build_missing_forward_text()

        if len(raw_forwards) > self._settings.max_forward_count:
            return None, build_too_many_forwards_text(self._settings.max_forward_count)

        forwarded_messages = extract_forward_list(
            message=message,
            limit=self._settings.max_forward_count,
        )
        if not forwarded_messages:
            return None, build_empty_forward_text()

        forwarded_messages = self._author_resolver.enrich_messages(forwarded_messages)

        theme = get_theme(self._state_store.get_style(user_id))
        request = QuoteRenderRequest(
            mode=RenderMode.THREAD,
            theme=theme,
            messages=forwarded_messages,
        )
        return request, None
