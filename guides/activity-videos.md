# Activity videos in the slideshow

Use the existing `activity.md` in each activity folder. No separate video Markdown file is required. In its opening front-matter block, replace `youtube: NA` with comma-separated YouTube links:

```text
youtube: https://www.youtube.com/watch?v=VIDEO_ID_1, https://youtu.be/VIDEO_ID_2
```

Publish the week normally with `py tools/publish_week.py`, then commit and push. Photos appear first in their existing order, followed by videos in link order. Repeated links to the same video produce only one video slide. Videos-only activities are supported. Leave `youtube: NA` when there are no videos.

Supported HTTPS URL forms: youtube.com/watch?v=..., youtu.be/..., and YouTube /shorts/, /live/, or /embed/ links. Video IDs must be 11 characters. Invalid or unsupported links are not embedded; the original generated links remain available. Timestamp and playlist parameters are not carried into the player.

Photos advance every three seconds while visible, except during hover, focus, touch, or reduced-motion settings. Video slides stop automatic advancement and require the visitor to press Play. Previous/Next remains available below the player. Leaving a video, hiding the page, scrolling the gallery out of view, or switching language unloads the player to stop its audio. Returning starts with a fresh player; playback position is not preserved.

Players use youtube-nocookie.com and are loaded only for the active visible video slide. This does not eliminate all third-party data processing. Keep the generated YouTube links as a fallback if embedding is restricted or blocked. Videos must be viewable by the audience and permit embedding.

The enhancement reads the existing YouTube links in activity tiles, so already-published pages gain video slides when the updated shared app.js is loaded. New or changed links still require republishing the affected week.

## Manual review checklist

Browser playback and layout have not been verified automatically. Before merging, check:

- Multiple photos followed by two different videos; correct counter and order.
- One photo plus a video, videos only, and photos only.
- Normal watch URLs, short links, Shorts links, duplicate links and invalid IDs.
- Photo timer stops on a video; Play is manual; Next stops the audio.
- Switching EN/PT, hiding the tab and scrolling away stops playback.
- Mobile swipe, portrait video layout, keyboard navigation and reduced motion.
- Original YouTube fallback links, sharing, subscriptions and comments still work.
