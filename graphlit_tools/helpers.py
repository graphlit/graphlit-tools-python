import asyncio
from typing import Callable, Optional, List, Any, Coroutine
from graphlit_api import enums

def format_person(person) -> List[str]:
    results = []

    results.append(f'**Person ID:** {person.id}')

    results.append(f'**Name:** {person.name}')

    if person.email is not None:
        results.append(f'**Email:** {person.email}')

    if person.uri is not None:
        results.append(f'**URI:** {person.uri}')

    if person.education is not None:
        results.append(f'**Education:** {person.education}')

    if person.occupation is not None:
        results.append(f'**Occupation:** {person.occupation}')

    results.append('\n')

    return results

def format_organization(organization) -> List[str]:
    results = []

    results.append(f'**Organization ID:** {organization.id}')

    results.append(f'**Name:** {organization.name}')

    if organization.email is not None:
        results.append(f'**Email:** {organization.email}')

    if organization.uri is not None:
        results.append(f'**URI:** {organization.uri}')

    results.append('\n')

    return results

def format_content(content, include_text: Optional[bool] = True) -> List[str]:
    results = []

    # Basic content details
    results.append(f"**Content ID:** {content.id}")

    if content.type == enums.ContentTypes.FILE:
        results.append(f"**File Type:** [{content.file_type}]")
        results.append(f"**File Name:** {content.file_name}")
    else:
        results.append(f"**Type:** [{content.type}]")
        if content.type not in [enums.ContentTypes.PAGE, enums.ContentTypes.EMAIL]:
            results.append(f"**Name:** {content.name}")

    # Optional metadata
    if content.uri:
        results.append(f"**URI:** {content.uri}")
    if content.creation_date:
        results.append(f"**Ingestion Date:** {content.creation_date}")
    if content.original_date:
        results.append(f"**Author Date:** {content.original_date}")

    # Issue details
    if content.issue:
        issue_attributes = [
            ("Title", content.issue.title),
            ("Identifier", content.issue.identifier),
            ("Type", content.issue.type),
            ("Project", content.issue.project),
            ("Team", content.issue.team),
            ("Status", content.issue.status),
            ("Priority", content.issue.priority),
        ]
        results.extend([f"**{label}:** {value}" for label, value in issue_attributes if value])

        if content.issue.labels:
            results.append(f"**Labels:** {', '.join(content.issue.labels)}")

    # Email details
    if content.email:
        email_attributes = [
            ("Subject", content.email.subject),
            ("Sensitivity", content.email.sensitivity.name if content.email.sensitivity else None),
            ("Priority", content.email.priority.name if content.email.priority else None),
            ("Importance", content.email.importance.name if content.email.importance else None),
            ("Labels", ', '.join(content.email.labels) if content.email.labels else None),
            ("To", ', '.join(f"{r.name} <{r.email}>" for r in content.email.to) if content.email.to else None),
            ("From", ', '.join(f"{r.name} <{r.email}>" for r in getattr(content.email, "from", []))),
            ("CC", ', '.join(f"{r.name} <{r.email}>" for r in content.email.cc) if content.email.cc else None),
            ("BCC", ', '.join(f"{r.name} <{r.email}>" for r in content.email.bcc) if content.email.bcc else None),
        ]
        results.extend([f"**{label}:** {value}" for label, value in email_attributes if value])

    # Document details
    if content.document:
        document_attributes = [
            ("Title", content.document.title),
            ("Author", content.document.author),
        ]
        results.extend([f"**{label}:** {value}" for label, value in document_attributes if value])

    # Audio details
    if content.audio:
        audio_attributes = [
            ("Title", content.audio.title),
            ("Host", content.audio.author),
            ("Episode", content.audio.episode),
            ("Series", content.audio.series),
        ]
        results.extend([f"**{label}:** {value}" for label, value in audio_attributes if value])

    # Links
    #if content.links:
    #    results.extend([f"**{link.link_type} Link:** {link.uri}" for link in content.links[:10]])

    # Include text content if specified
    if include_text:
        if content.pages:
            for page in content.pages:
                if page.chunks:
                    results.append(f"**Page #{page.index + 1}:**")
                    results.extend([chunk.text for chunk in page.chunks])
                    results.append("\n---\n")

        if content.segments:
            for segment in content.segments:
                results.append(f"**Transcript Segment [{segment.start_time}-{segment.end_time}]:**")
                results.append(segment.text)
                results.append("\n---\n")

        if not content.pages and not content.segments and content.markdown:
            results.append(content.markdown)
            results.append("\n")
    else:
        results.append("\n")

    return results

def run_async(coro_func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs) -> Any:
    """
    Runs an async function synchronously, handling event loops properly.

    Args:
        coro_func: The asynchronous function to be run.
        *args: Positional arguments to pass to the async function.
        **kwargs: Keyword arguments to pass to the async function.

    Returns:
        The result of the async function execution.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If the loop is already running, ensure the coroutine runs within it
            return loop.run_until_complete(coro_func(*args, **kwargs))
        else:
            # If no loop is running, use asyncio.run
            return asyncio.run(coro_func(*args, **kwargs))
    except RuntimeError:
        # Handle case where the event loop is closed
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(coro_func(*args, **kwargs))
