"""HowLongToBeat game duration result entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HltbResult:
    """Game completion time data from HowLongToBeat.

    All durations are in hours, rounded to one decimal place.
    A value of ``None`` means no data is available for that completion style.

    Args:
        main_story: Time to complete the main story.
        main_extra: Time to complete main story plus extras.
        completionist: Time to 100% complete the game.
    """

    main_story: float | None
    main_extra: float | None
    completionist: float | None
