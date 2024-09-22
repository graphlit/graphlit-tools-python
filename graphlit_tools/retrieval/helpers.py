from typing import List, Optional
from graphlit_api import enums

def format_content(content, include_text: Optional[bool] = True) -> List[str]:
    results = []

    results.append(f'**Content ID:** {content.id}')

    if content.type == enums.ContentTypes.FILE:
        results.append(f'**File Type:** [{content.file_type}]')
        results.append(f'**File Name:** {content.file_name}')
    else:
        results.append(f'**Type:** [{content.type}]')

        if content.type is not enums.ContentTypes.PAGE:
            results.append(f'**Name:** {content.name}')

    if content.uri is not None:
        results.append(f'**URI:** {content.uri}')

    if content.creation_date is not None:
        results.append(f'**Ingestion Date:** {content.creation_date}')

    if content.original_date is not None:
        results.append(f'**Author Date:** {content.original_date}')

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
