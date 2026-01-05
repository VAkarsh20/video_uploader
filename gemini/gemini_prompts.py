GEMINI_GENERATE_DESCRIPTION_PROMPT = """
Write me captions for {topic} on Tiktok/Instagram Reels/Youtube Shorts. Focus on SEO optimization, Keyword usage, and Grammar/spelling. I am providing both my transcript for the video as well as a previous example captions from Tiktok to give you an idea of formatting:

TRANSCRIPT:
{transcript}

EXAMPLE CAPTION 1: {title1}
{caption1}

EXAMPLE CAPTION 2: {title2}
{caption2}

EXAMPLE CAPTION 3: {title3}
{caption3}
"""

GEMINI_PROOFREAD_DESCRIPTION_PROMPT = """
How is this caption? This is my rough draft after getting inspiration from GEMINI. Focus in Keyword usage, SEO Optimization, Spelling and Grammar, and not using and words that would hurt the algorithm.
"""
