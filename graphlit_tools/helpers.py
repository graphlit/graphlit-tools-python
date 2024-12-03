from typing import List, Optional
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

    results.append(f'**Content ID:** {content.id}')

    if content.type == enums.ContentTypes.FILE:
        results.append(f'**File Type:** [{content.file_type}]')
        results.append(f'**File Name:** {content.file_name}')
    else:
        results.append(f'**Type:** [{content.type}]')

        if content.type is not enums.ContentTypes.PAGE and content.type is not enums.ContentTypes.EMAIL:
            results.append(f'**Name:** {content.name}')

    if content.uri is not None:
        results.append(f'**URI:** {content.uri}')

    if content.creation_date is not None:
        results.append(f'**Ingestion Date:** {content.creation_date}')

    if content.original_date is not None:
        results.append(f'**Author Date:** {content.original_date}')

    if content.issue is not None:
        if content.issue.title is not None:
            results.append(f'**Title:** {content.issue.title}')

        if content.issue.identifier is not None:
            results.append(f'**Identifier:** {content.issue.identifier}')

        if content.issue.type is not None:
            results.append(f'**Type:** {content.issue.type}')

        if content.issue.project is not None:
            results.append(f'**Project:** {content.issue.project}')

        if content.issue.team is not None:
            results.append(f'**Team:** {content.issue.team}')

        if content.issue.status is not None:
            results.append(f'**Status:** {content.issue.status}')

        if content.issue.priority is not None:
            results.append(f'**Priority:** {content.issue.priority}')

        if content.issue.labels is not None:
            results.append(f'**Labels:** {', '.join(content.issue.labels)}')

    if content.email is not None:
        if content.email.subject is not None:
            results.append(f'**Subject:** {content.email.subject}')

        if content.email.labels is not None:
            results.append(f'**Labels:** {', '.join(content.email.labels)}')

        if content.email.to is not None:
            results.append(f'**To:** {', '.join(f"{recipient.name} <{recipient.email}>" for recipient in content.email.to)}')

        if getattr(content.email, 'from', None) is not None:
            results.append(f"**From:** {', '.join(f'{recipient.name} <{recipient.email}>' for recipient in getattr(content.email, 'from'))}")

        if content.email.cc is not None:
            results.append(f'**CC:** {', '.join(f"{recipient.name} <{recipient.email}>" for recipient in content.email.cc)}')

        if content.email.bcc is not None:
            results.append(f'**BCC:** {', '.join(f"{recipient.name} <{recipient.email}>" for recipient in content.email.bcc)}')

    if content.document is not None:
        if content.document.title is not None:
            results.append(f'**Title:** {content.document.title}')

        if content.document.author is not None:
            results.append(f'**Author:** {content.document.author}')

    if content.audio is not None:
        if content.audio.title is not None:
            results.append(f'**Title:** {content.audio.title}')

        if content.audio.author is not None:
            results.append(f'**Host:** {content.audio.author}')

        if content.audio.episode is not None:
            results.append(f'**Episode:** {content.audio.episode}')

        if content.audio.series is not None:
            results.append(f'**Series:** {content.audio.series}')

    if content.links is not None:
        for link in content.links[:10]: # NOTE: just return top 10 links
            results.append(f'**{link.link_type} Link:** {link.uri}')

    if include_text is True:
        results.append('\n')

        if content.pages is not None:
            for page in content.pages:
                if page.chunks is not None and len(page.chunks) > 0:
                    results.append(f'**Page #{page.index + 1}**:')

                    for chunk in page.chunks:
                        results.append(chunk.text)

                    results.append('\n---\n')

        if content.segments is not None:
            for segment in content.segments:
                results.append(f'**Transcript Segment [{segment.start_time}-{segment.end_time}]**:')
                results.append(segment.text)

                results.append('\n---\n')

        if content.pages is None and content.segments is None:
            if content.markdown is not None:
                results.append(content.markdown)

                results.append('\n')
    else:
        results.append('\n')

    return results
