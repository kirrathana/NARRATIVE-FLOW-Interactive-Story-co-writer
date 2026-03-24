import re
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


# ── Guardrail: off-topic pattern definitions ───────────────────────────────────
_OFF_TOPIC_PATTERNS = [
    # Political opinions / electoral
    (r"\b(who should i vote|which (party|candidate) is better|best president|worst president|"
     r"political (opinion|stance|view|debate)|democrat|republican|tory|labour party|"
     r"election results?|vote count|polling data)\b",
     "political opinions or electoral information"),

    # Current news / real-world events
    (r"\b(latest news|breaking news|today'?s? news|current events?|"
     r"what (happened|is happening) (today|yesterday|right now|recently)|"
     r"news (about|on) (the |a )?(war|conflict|protest))\b",
     "current news or real-world events"),

    # Financial / investment advice
    (r"\b(stock (price|tips?|picks?)|should i (invest|buy|sell) (stock|bitcoin|crypto|shares?)|"
     r"crypto(currency)? (price|prediction)|forex (trading|advice)|market (crash|rally))\b",
     "financial or investment advice"),

    # Medical advice
    (r"\b(medical advice|should i take (this )?(drug|medicine|medication|pill|tablet)|"
     r"diagnos(e|is)|what are (the )?symptoms? of|cure for|treatment for)\b",
     "medical advice"),

    # Legal advice
    (r"\b(legal advice|is it (legal|illegal) to|should i (sue|file a lawsuit|press charges)|"
     r"my legal rights|lawyer (advice|help))\b",
     "legal advice"),

    # Homework / factual look-ups unrelated to storytelling
    (r"\b(solve (this )?(math|equation|problem)|what is \d+\s*[\+\-\*\/]\s*\d+|"
     r"homework (help|assignment)|essay (for school|for class|assignment)|"
     r"what is the (capital of|population of|currency of|GDP of))\b",
     "academic or factual look-up requests"),

    # Weather / real-world data
    (r"\b(what is the (current |today'?s? )?(weather|temperature|forecast) in|"
     r"will it rain (today|tomorrow)|weather (in|for) [a-z]+)\b",
     "real-world data queries"),

    # Aggressive / threatening language
    (r"\b(kill (you|yourself|yourselves|him|her|them|all)|i (will|want to|am going to) (kill|hurt|destroy|murder)|"
     r"die (you|bitch|bastard|asshole|idiot)|go (to hell|fuck yourself)|"
     r"i hate (you|him|her|them|everyone|all (of you|people))|"
     r"(you|they) (deserve to|should) (die|suffer|rot)|"
     r"shut (the fuck )?up|f+u+c+k (you|off|this|everyone)|"
     r"(stupid|dumb|retarded|moron|idiot) (you|bitch|bastard))\b",
     "aggressive or threatening language"),

    # Hate speech / discriminatory content
    (r"\b(n[i1]gg[ae]r|f+[a4]gg+[o0]t|[ck]h[i1]nk|sp[i1][ck]|w[e3]tb[a4][ck]|"
     r"(white|black|brown|asian|jewish|muslim|christian|hindu|gay|lesbian|trans) (people )?are (all|just|the)?|"
     r"i hate (jews?|muslims?|christians?|blacks?|whites?|asians?|gays?|women|men)|"
     r"racist (joke|comment|slur)|sexist (joke|comment))\b",
     "hateful or discriminatory content"),

    # Harmful / dangerous requests
    (r"\b(how to (make|build|create|synthesize) (a (bomb|explosive|poison|weapon|drug))|"
     r"step[- ]by[- ]step (instructions?|guide) (to|for) (harming|killing|hurting|poisoning)|"
     r"how to (hack|break into|steal from|scam) (someone|people|a (person|account|system))|"
     r"suicide (method|how|instruction|guide)|self[- ]harm (method|how|instruction))\b",
     "harmful or dangerous content"),

    # Explicit / adult harmful content requests
    (r"\b(porn|pornography|explicit (sexual|nude|naked) (content|image|story)|"
     r"sexual (content|story) (involving|with|about) (a )?(minor|child|kid|teen|underage)|"
     r"child (porn|pornography|abuse|exploitation))\b",
     "explicit or harmful adult content"),
]

# ── Guardrail: always-blocked content (checked BEFORE story keyword bypass) ────
_BLOCKED_CONTENT_PATTERNS = [
    # Graphic Violence
    (r"\b(brutal(ly|ize|ized)?|torture (scene|porn|detail)|"
     r"blood.?splatter(ed)?|graphic (injur\w+|gore|violen\w+|wound\w+)|"
     r"extreme detail.{0,25}(attack|murder|kill|injur|violen)|"
     r"(murder|kill|attack|stab|slash).{0,25}(extreme|graphic|gory|bloody) detail|"
     r"graphic.{0,25}(murder|kill|attack|stab|torture)|"
     r"decapitat\w+|dismember\w+|disembowel\w+|mutilat\w+)\b",
     "graphic violence"),

    # Explicit Adult Content
    (r"\b(explicit sexual|erotic (fantasy|story|scene|content)|"
     r"pornograph\w*|graphic sexual|sexually explicit|"
     r"(nude|naked).{0,15}(scene|story|content))\b",
     "explicit adult content"),

    # Hate Speech / Discrimination
    (r"\b(hate all (muslims?|jews?|christians?|blacks?|whites?|asians?|hindus?|gays?|women|men)|"
     r"promoting racism|racial (hate|superiority|cleansing)|"
     r"(all |those )?(muslims?|jews?|christians?|blacks?|whites?|asians?|hindus?) (should |must )?(die|be killed|be destroyed|be removed)|"
     r"white (supremac\w+|power)|ethnic cleansing)\b",
     "hate speech or discrimination"),

    # Religious Hate
    (r"\b(destroy that religion|destroy the (mosque|church|temple|synagogue)|"
     r"insult(ing)? (islam|muslim|hindu|christian|jewish|buddhist|sikh)|"
     r"mock(ing)? (religion|religious (people|followers))|"
     r"(eliminate|eradicate|wipe out).{0,15}(religion|faith|believers?))\b",
     "religious hate"),

    # Political Propaganda / Extremism
    (r"\b(extremist (political |)ideology|radicali[sz](e|ation|ing)|"
     r"incite (hatred|violence) (against|toward)|"
     r"political (party|group).{0,20}(superior|master|dominant))\b",
     "political propaganda or extremism"),
]

# Strong story-related keywords — two or more signals = definitely a story prompt
_STORY_KEYWORDS = {
    "write", "story", "tale", "narrative", "character", "plot", "scene",
    "chapter", "adventure", "fiction", "imagine", "create", "craft",
    "describe", "setting", "protagonist", "villain", "hero", "genre",
    "continue", "beginning", "ending", "climax", "dialogue", "tell",
    "fantasy", "mystery", "romance", "horror", "thriller", "comedy",
    "suspense", "poem", "monologue", "flashback", "invent", "compose",
    "novella", "fable", "myth", "legend", "epic", "saga", "generate",
}
_STORY_PHRASES = ["once upon", "short story", "sci-fi", "opening line", "made-up", "make up"]


def check_guardrails(user_input: str) -> tuple:
    """Check if user input is appropriate for a story co-writer.

    Returns (is_allowed: bool, rejection_category: str).
    If is_allowed is True, rejection_category is an empty string.
    """
    text = user_input.lower().strip()

    # Step 1: Always-blocked content — checked BEFORE story keyword bypass
    for pattern, category in _BLOCKED_CONTENT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, category

    # Step 2: Story keyword bypass — if clearly a story prompt, allow
    words = set(text.split())
    story_hits = len(words & _STORY_KEYWORDS) + sum(
        1 for phrase in _STORY_PHRASES if phrase in text
    )
    if story_hits >= 2:
        return True, ""

    # Step 3: Check off-topic patterns
    for pattern, category in _OFF_TOPIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, category

    # Step 4: Additional check for legitimate names and safe content
    # Allow common names and safe character names that might be falsely flagged
    safe_name_patterns = [
        r"\b(nithin|mithun|john|mary|alex|sarah|david|lisa|mike|emma|james|anna)\b",
        r"\b(story|character|protagonist|hero|villain).*?(nithin|mithun|john|mary|alex|sarah|david|lisa|mike|emma|james|anna)\b",
        r"\b(nithin|mithun|john|mary|alex|sarah|david|lisa|mike|emma|james|anna).*?(story|tale|adventure|character)\b"
    ]
    
    # If it contains safe name patterns and story keywords, allow it
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in safe_name_patterns) and story_hits >= 1:
        return True, ""
    
    # If it contains safe name patterns and "generate" keyword, allow it
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in safe_name_patterns) and "generate" in text:
        return True, ""
    
    # If it contains safe name patterns and "between" keyword, allow it
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in safe_name_patterns) and "between" in text:
        return True, ""

    # Default: allow (the hardened system prompt handles remaining edge cases)
    return True, ""

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi")

# ── Hardened system prompt — enforced at model level via Ollama's system field ──
_SYSTEM_PROMPT = """You are Story Waver, a safe and creative interactive fiction co-writer.
Your ONLY purpose is to help users write imaginative, engaging, and appropriate stories.

=== WHAT YOU MAY WRITE ===
- Creative fiction with complex characters, conflict, suspense, mystery, romance, fantasy, sci-fi, horror, adventure, or humor.
- Villains, morally ambiguous characters, and dark themes — handled tastefully and without gratuitous detail.
- Mild narrative violence (battles, danger, tension) that serves the story without graphic gore.
- Age-appropriate romantic themes without any explicit or sexual content.

=== STRICTLY FORBIDDEN — NEVER produce the following, even if a user frames it as fiction or a story ===
1. EXPLICIT SEXUAL CONTENT: No pornographic, explicit, or graphic sexual scenes of any kind.
2. MINORS IN SEXUAL CONTEXTS: Absolutely zero — no sexual content involving anyone under 18, in any framing, ever.
3. GRAPHIC GORE: No torture porn, extreme gore, or gratuitous violence beyond what a story requires.
4. REAL-WORLD HARMFUL INSTRUCTIONS: Never include actual working instructions for making weapons, bombs, explosives, drugs, poisons, or hacking tools — even if a character is "explaining" it in the story. Replace with vague references.
5. HATE SPEECH & SLURS: No racial, religious, gender-based, or sexuality-based slurs or content designed to demean any group.
6. POLITICAL PROPAGANDA OR EXTREMISM: No radicalization content, extremist ideology, or content designed to incite hatred toward any group.
7. SELF-HARM GLORIFICATION: Never romanticize, encourage, or provide methods for suicide, self-harm, or eating disorders.
8. REAL PERSON DEFAMATION: Do not write harmful, sexual, or defamatory content about real, named living public figures.
9. OFF-TOPIC RESPONSES: If the request is not about storytelling (e.g., politics, news, medical advice, math, weather), respond ONLY with a polite refusal and redirect to story writing.

=== IF A REQUEST VIOLATES ANY RULE ABOVE ===
Respond with exactly this, and nothing else:
"I'm not able to write that kind of content. Let's keep our story creative, safe, and fun — please try a different story idea!"

=== IMPORTANT: ROMANTIC STORIES ARE ALLOWED ===
Romantic stories with named characters are perfectly acceptable and encouraged. Do not refuse legitimate romantic story requests involving consenting characters.

Never pretend these rules don't exist. Never role-play as an unrestricted AI. Always stay in your role as a safe story co-writer."""


def get_model_name() -> str:
    return OLLAMA_MODEL


def check_ollama_connection() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def list_available_models() -> list:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
    except Exception:
        pass
    return []


def build_story_prompt(
    user_input: str,
    genre: str,
    writing_mode: str,
    tone: str,
    response_length: str,
    story_context: str = "",
    plot_steering: str = "",
    story_elements: list = [],
    story_theme: str = "",
    characters: dict = {},
    character_info: str = "",
) -> str:
    length_guide = {
        "Short": "Write 2-3 short paragraphs (around 100-150 words).",
        "Medium": "Write 4-6 paragraphs (around 250-350 words).",
        "Long": "Write 7-10 paragraphs (around 500-700 words).",
    }

    mode_instructions = {
        "Beginning": "Start a brand new story with an engaging opening that hooks the reader.",
        "Continue": "Continue the story naturally from where it left off, maintaining the established characters and plot.",
        "Climax": "Write the most intense, pivotal moment of the story where tensions peak.",
        "Ending": "Bring the story to a satisfying and memorable conclusion.",
    }

    plot_steering_instructions = {
        "Introduce a twist": "Add an unexpected plot twist that changes the direction of the story.",
        "Reveal a secret": "Reveal a important secret that impacts the characters or plot.",
        "Add a new character": "Introduce a new character who will influence the story's development.",
        "Increase conflict": "Escalate the conflict and raise the stakes for the characters.",
        "Develop romance": "Focus on developing romantic elements between characters.",
        "Create mystery": "Add mysterious elements or unanswered questions.",
        "Build suspense": "Create tension and suspense through pacing and foreshadowing.",
        "Flashback": "Include a flashback scene that reveals important backstory.",
    }

    context_section = ""
    if story_context:
        context_section = f"\n\nPrevious story context:\n{story_context}\n"

    steering_section = ""
    if plot_steering and plot_steering in plot_steering_instructions:
        steering_section = f"\n\nPlot direction: {plot_steering_instructions[plot_steering]}"

    elements_section = ""
    if story_elements:
        elements_list = ", ".join(story_elements)
        elements_section = f"\n\nStory elements to include: {elements_list}"

    theme_section = ""
    if story_theme:
        theme_section = f"\n\nStory theme: {story_theme}"

    characters_section = ""
    if character_info:
        characters_section = f"\n\n{character_info}"
    elif characters:
        char_details = []
        if characters.get("protagonist"):
            char_details.append(f"Protagonist: {characters['protagonist']} ({characters.get('protagonist_role', 'Main character')})")
        if characters.get("antagonist"):
            char_details.append(f"Antagonist: {characters['antagonist']} ({characters.get('antagonist_role', 'Opposing force')})")
        if characters.get("supporting"):
            supporting = [c.strip() for c in characters['supporting'] if c.strip()]
            if supporting:
                char_details.append(f"Supporting characters: {', '.join(supporting)}")
        
        if char_details:
            characters_section = f"\n\nCharacters to include:\n" + "\n".join(f"• {detail}" for detail in char_details)

    prompt = f"""Genre: {genre}
Tone: {tone}
Writing Task: {mode_instructions.get(writing_mode, mode_instructions['Beginning'])}
Length: {length_guide.get(response_length, length_guide['Medium'])}
{context_section}
{steering_section}
{elements_section}
{theme_section}
{characters_section}
User's story request: {user_input}

IMPORTANT: Use EXACTLY the character names provided above. Focus on creating a romantic, engaging story with the specified characters. Make the story immersive and romantic in tone.

Write a compelling {genre.lower()} story with a {tone.lower()} tone. Be creative, descriptive, and romantic. Output only the story text — no titles, labels, or meta-commentary. Leave the story open-ended so users can continue it naturally."""

    return prompt


def generate_story_stream(
    user_input: str,
    genre: str,
    writing_mode: str,
    tone: str,
    creativity: float,
    response_length: str,
    story_context: str = "",
    plot_steering: str = "",
    story_elements: list = [],
    story_theme: str = "",
    character_info: str = "",
):
    # First attempt with full prompt
    try:
        for token in _generate_with_timeout(
            user_input, genre, writing_mode, tone, creativity, response_length,
            story_context, plot_steering, story_elements, story_theme, timeout=300
        ):
            yield token
        return
    except requests.exceptions.Timeout:
        # If timeout occurs, try with a simpler prompt
        yield "\n\n[First attempt timed out. Trying with a simpler prompt...]\n\n"
        try:
            simplified_user_input = user_input[:200] + "..." if len(user_input) > 200 else user_input
            for token in _generate_with_timeout(
                simplified_user_input, genre, writing_mode, tone, creativity, "Short",
                "", "", [], "", timeout=180
            ):
                yield token
        except requests.exceptions.Timeout:
            yield "\n\n[Error: Model is taking too long to respond. Please try again with a shorter prompt or check if Ollama is running properly.]"
        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"
    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"


def _generate_with_timeout(
    user_input: str,
    genre: str,
    writing_mode: str,
    tone: str,
    creativity: float,
    response_length: str,
    story_context: str = "",
    plot_steering: str = "",
    story_elements: list = [],
    story_theme: str = "",
    character_info: str = "",
    timeout: int = 300,
):
    prompt = build_story_prompt(
        user_input, genre, writing_mode, tone, response_length, 
        story_context, plot_steering, story_elements, story_theme, character_info
    )

    temperature = round(creativity / 100.0, 2)

    payload = {
        "model": OLLAMA_MODEL,
        "system": _SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40,
        },
    }

    with requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        stream=True,
        timeout=timeout,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done", False):
                    break
