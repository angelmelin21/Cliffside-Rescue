
import random
import html
import time
import json
import os
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from questions import questions

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cliffside Rescue",
    page_icon="🧗",
    layout="wide"
)

TOTAL_QUESTIONS = 10
ROPE_MAX = 10
MIN_RESCUE_LEVEL = 8
TIME_LIMIT = 30
LEADERBOARD_FILE = "leaderboard.json"

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}
div[data-testid="column"] {
    min-width: 0;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
}
div.stButton > button {
    border-radius: 10px;
    min-height: 44px;
    font-weight: 600;
}
.scene-title {
    text-align: center;
    font-size: 25px;
    font-weight: bold;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# QUESTION HELPERS
# ---------------------------------------------------------
def get_question_text(q):
    return q.get("question", q.get("q", "Question unavailable"))


def get_options(q):
    return q.get("options", q.get("choices", q.get("answers", [])))


def get_correct_answer(q):
    return q.get("answer", q.get("correct_answer", q.get("correct", "")))


def get_explanation(q):
    return q.get("explanation", "")


def get_difficulty(q):
    return str(q.get("difficulty", "Easy")).capitalize()


# NEW: Count questions by difficulty.
def get_question_counts():
    return {
        level: sum(
            1 for q in questions
            if get_difficulty(q) == level
        )
        for level in ["Easy", "Medium", "Hard"]
    }


# NEW: Dropdown to view all questions.
def display_all_questions():
    counts = get_question_counts()

    st.markdown("---")
    st.markdown("## 📚 Question Bank")
    st.caption(
        "Browse all available questions below. "
        "Only questions from your selected difficulty are randomly "
        "chosen when you start a game."
    )

    st.markdown(
        f"**Total questions available: {len(questions)}**"
    )

    count_col1, count_col2, count_col3 = st.columns(3)

    with count_col1:
        st.metric("🟢 Easy Questions", counts["Easy"])

    with count_col2:
        st.metric("🟡 Medium Questions", counts["Medium"])

    with count_col3:
        st.metric("🔴 Hard Questions", counts["Hard"])

    with st.expander("📖 View all questions", expanded=False):
        tabs = st.tabs([
            f"🟢 Easy ({counts['Easy']})",
            f"🟡 Medium ({counts['Medium']})",
            f"🔴 Hard ({counts['Hard']})"
        ])

        levels = ["Easy", "Medium", "Hard"]

        for tab, level in zip(tabs, levels):
            with tab:
                level_questions = [
                    q for q in questions
                    if get_difficulty(q) == level
                ]

                if not level_questions:
                    st.info(
                        f"No {level.lower()} questions are available."
                    )
                    continue

                for number, q in enumerate(level_questions, start=1):
                    st.markdown(
                        f"**{number}. {get_question_text(q)}**"
                    )

                    options = get_options(q)

                    if options:
                        for option in options:
                            st.write(f"- {option}")

                    correct_answer = get_correct_answer(q)

                    if correct_answer:
                        st.caption(
                            f"Correct answer: {correct_answer}"
                        )

                    explanation = get_explanation(q)

                    if explanation:
                        st.caption(f"Explanation: {explanation}")

                    if number < len(level_questions):
                        st.divider()


# ---------------------------------------------------------
# LEADERBOARD
# ---------------------------------------------------------
def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
            entries = json.load(file)

        return entries if isinstance(entries, list) else []

    except (json.JSONDecodeError, OSError):
        return []


def save_leaderboard(entries):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
        json.dump(entries, file, indent=4, ensure_ascii=False)


def sort_leaderboard(entries):
    return sorted(
        entries,
        key=lambda entry: (
            int(entry.get("score", 0)),
            int(entry.get("correct", 0))
        ),
        reverse=True
    )


def record_leaderboard_score():
    if st.session_state.score_saved:
        return

    correct_count = sum(
        1 for answer in st.session_state.answers
        if answer["is_correct"]
    )

    entries = load_leaderboard()

    entries.append({
        "name": st.session_state.player_name,
        "score": int(st.session_state.score),
        "difficulty": st.session_state.difficulty,
        "correct": correct_count,
        "date": time.strftime("%d %b %Y, %I:%M %p")
    })

    save_leaderboard(sort_leaderboard(entries))
    st.session_state.score_saved = True


def display_leaderboard():
    st.markdown("---")
    st.markdown("## 🏆 Leaderboard")
    st.caption("The highest scorer always appears first.")

    entries = sort_leaderboard(load_leaderboard())

    if not entries:
        st.info(
            "No scores yet! Complete a game to appear on the leaderboard."
        )
        return

    leaderboard_rows = []

    for rank, entry in enumerate(entries, start=1):
        if rank == 1:
            rank_display = "🥇"
        elif rank == 2:
            rank_display = "🥈"
        elif rank == 3:
            rank_display = "🥉"
        else:
            rank_display = rank

        leaderboard_rows.append({
            "Rank": rank_display,
            "Player": entry.get("name", "Player"),
            "Score": int(entry.get("score", 0)),
            "Difficulty": entry.get("difficulty", "-"),
            "Correct Answers": f"{entry.get('correct', 0)}",
            "Date": entry.get("date", "-")
        })

    st.dataframe(
        leaderboard_rows,
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------
# DRAW CLIFFSIDE SCENE
# ---------------------------------------------------------
def draw_scene(rope_level, won=False):
    rope_level = max(0, min(ROPE_MAX, int(rope_level)))

    rope_blocks = ""

    if not won:
        for i in range(rope_level):
            y = 178 + i * 32
            rope_blocks += f"""
            <rect x="344" y="{y}" width="22" height="27"
                  rx="4" fill="#f3c969"
                  stroke="#fff0b3" stroke-width="2"/>
            """

    if won:
        people = """
        <!-- Rescuer -->
        <g stroke-linecap="round" stroke-linejoin="round">
          <circle cx="85" cy="90" r="20"
                  fill="#f0bd91" stroke="#382d35" stroke-width="3"/>
          <path d="M65 86 Q65 64 85 68 Q104 68 105 88
                   L96 79 Q82 87 69 79 Z" fill="#342b31"/>
          <path d="M68 113 L65 145 L101 145 L98 113 Z"
                fill="#ed765b" stroke="#382d35" stroke-width="3"/>
          <path d="M70 120 L57 103 L48 83"
                stroke="#f0bd91" stroke-width="9" fill="none"/>
          <path d="M96 120 L111 103 L119 83"
                stroke="#f0bd91" stroke-width="9" fill="none"/>
          <path d="M74 145 L70 164 M92 145 L97 164"
                stroke="#263b55" stroke-width="10"/>
          <path d="M64 165 L75 165 M92 165 L103 165"
                stroke="#222b37" stroke-width="7"/>
        </g>

        <!-- Rescued friend -->
        <g stroke-linecap="round" stroke-linejoin="round">
          <circle cx="174" cy="90" r="20"
                  fill="#f0bd91" stroke="#382d35" stroke-width="3"/>
          <path d="M154 86 Q154 64 174 68 Q193 68 194 88
                   L185 79 Q171 87 158 79 Z" fill="#342b31"/>
          <path d="M157 113 L154 145 L190 145 L187 113 Z"
                fill="#72c9e8" stroke="#263b55" stroke-width="3"/>
          <path d="M159 120 L146 103 L138 83"
                stroke="#f0bd91" stroke-width="9" fill="none"/>
          <path d="M185 120 L200 103 L208 83"
                stroke="#f0bd91" stroke-width="9" fill="none"/>
          <path d="M163 145 L159 164 M181 145 L186 164"
                stroke="#263b55" stroke-width="10"/>
          <path d="M153 165 L164 165 M181 165 L192 165"
                stroke="#222b37" stroke-width="7"/>
        </g>

        <rect x="22" y="215" width="230" height="75"
              rx="15" fill="#123c36"
              stroke="#79e0a2" stroke-width="2"/>
        <text x="137" y="245" fill="#a8ffc7"
              font-size="17" font-weight="bold"
              text-anchor="middle">RESCUE COMPLETE!</text>
        <text x="137" y="270" fill="#ffffff"
              font-size="14" text-anchor="middle">Everyone is safe!</text>
        """

    else:
        people = """
        <!-- Rescuer remains at the cliff edge -->
        <g stroke-linecap="round" stroke-linejoin="round">
          <circle cx="195" cy="91" r="23"
                  fill="#f0bd91" stroke="#382d35" stroke-width="4"/>
          <path d="M173 88 Q173 63 196 65 Q219 65 219 91
                   L212 81 Q194 89 178 80 Z" fill="#342b31"/>
          <path d="M181 118 L176 160 L215 160 L210 118 Z"
                fill="#ed765b" stroke="#382d35" stroke-width="4"/>
          <path d="M183 126 L215 143 L238 166"
                fill="none" stroke="#f0bd91" stroke-width="12"/>
          <path d="M208 127 L222 145"
                fill="none" stroke="#f0bd91" stroke-width="12"/>
          <path d="M185 158 L181 185 L164 185
                   M207 158 L214 183 L229 183"
                fill="none" stroke="#263b55" stroke-width="13"/>
          <path d="M165 185 L181 185 M215 183 L231 183"
                stroke="#222b37" stroke-width="9"/>
        </g>

        <!-- Friend remains at the same height -->
        <g stroke-linecap="round" stroke-linejoin="round">
          <circle cx="355" cy="550" r="23"
                  fill="#f0bd91" stroke="#382d35" stroke-width="4"/>
          <path d="M332 547 Q333 523 356 525 Q378 525 379 550
                   L371 540 Q353 548 337 539 Z" fill="#342b31"/>
          <path d="M340 576 L337 616 L373 616 L370 576 Z"
                fill="#72c9e8" stroke="#263b55" stroke-width="4"/>
          <path d="M341 585 L326 559 L355 515
                   M369 585 L382 559 L355 515"
                fill="none" stroke="#f0bd91" stroke-width="11"/>
          <circle cx="355" cy="515" r="8"
                  fill="#f0bd91" stroke="#382d35" stroke-width="3"/>
          <path d="M346 615 L338 650 M364 615 L375 650"
                stroke="#263b55" stroke-width="12" fill="none"/>
          <path d="M330 652 L340 650 M371 650 L382 652"
                stroke="#222b37" stroke-width="9"/>
        </g>

        <rect x="20" y="205" width="190" height="38"
              rx="12" fill="#15263b"/>
        <text x="115" y="230" fill="#ffffff"
              font-size="16" font-weight="bold"
              text-anchor="middle">RESCUER</text>

        <rect x="365" y="675" width="160" height="38"
              rx="12" fill="#15263b"/>
        <text x="445" y="700" fill="#ffffff"
              font-size="16" font-weight="bold"
              text-anchor="middle">YOUR FRIEND</text>
        """

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         width="100%" viewBox="0 0 560 900"
         preserveAspectRatio="xMidYMin meet">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#10243f"/>
          <stop offset="100%" stop-color="#244f70"/>
        </linearGradient>
        <linearGradient id="cliff" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#78818b"/>
          <stop offset="100%" stop-color="#333d4a"/>
        </linearGradient>
      </defs>

      <rect width="560" height="900" rx="18" fill="url(#sky)"/>

      <g fill="#ffffff" opacity="0.75">
        <circle cx="390" cy="70" r="2"/>
        <circle cx="480" cy="130" r="2"/>
        <circle cx="320" cy="105" r="2"/>
        <circle cx="510" cy="260" r="2"/>
        <circle cx="410" cy="330" r="1.5"/>
        <circle cx="475" cy="420" r="1.5"/>
      </g>

      <!-- Cliff -->
      <path d="M0 165 L245 165 L245 900 L0 900 Z" fill="url(#cliff)"/>
      <path d="M0 150 L258 150 L258 180 L0 180 Z" fill="#91a4a7"/>
      <path d="M0 150 L258 150" stroke="#c7d8d4" stroke-width="7"/>

      <g stroke="#9ca6ad" stroke-width="3" opacity="0.35" fill="none">
        <path d="M25 225 L90 255 L50 300"/>
        <path d="M140 340 L205 380 L165 420"/>
        <path d="M20 500 L100 540 L55 590"/>
        <path d="M125 680 L200 720 L155 770"/>
      </g>

      <!-- Rope connector from rescuer's hand -->
      {"<path d='M238 166 L355 166' stroke='#f3c969' stroke-width='7' stroke-linecap='round'/>" if not won else ""}

      {rope_blocks}
      {people}

      <text x="280" y="845" fill="#ffffff"
            font-size="19" font-weight="bold"
            text-anchor="middle">
        {"RESCUE SUCCESSFUL!" if won else f"ROPE LEVEL: {rope_level}/10"}
      </text>
      <text x="280" y="875" fill="#d6e6f2"
            font-size="14" text-anchor="middle">
        {"Both friends are safe!" if won else "Correct = +1 block | Wrong = -1 block"}
      </text>
    </svg>
    """

    components.html(svg, height=850, scrolling=False)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
defaults = {
    "started": False,
    "game_over": False,
    "won": False,
    "player_name": "",
    "difficulty": "",
    "difficulty_selected": False,
    "game_questions": [],
    "current": 0,
    "score": 0,
    "rope_level": 0,
    "answers": [],
    "feedback": "",
    "answered": False,
    "game_id": 0,
    "started_at": 0.0,
    "score_saved": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# GAME FUNCTIONS
# ---------------------------------------------------------
def start_game():
    st.session_state.game_id += 1
    st.session_state.started = True
    st.session_state.game_over = False
    st.session_state.won = False
    st.session_state.current = 0
    st.session_state.score = 0
    st.session_state.rope_level = 0
    st.session_state.answers = []
    st.session_state.feedback = ""
    st.session_state.answered = False
    st.session_state.started_at = time.time()
    st.session_state.score_saved = False

    available = [
        q for q in questions
        if get_difficulty(q) == st.session_state.difficulty
    ]

    if not available:
        available = list(questions)

    st.session_state.game_questions = random.sample(
        available, min(TOTAL_QUESTIONS, len(available))
    )


def answer_question(selected, timed_out=False):
    if st.session_state.answered:
        return

    q = st.session_state.game_questions[st.session_state.current]
    correct = get_correct_answer(q)

    if timed_out:
        is_correct = False
        selected_answer = "Time ran out"
        st.session_state.rope_level = max(
            0, st.session_state.rope_level - 1
        )
        st.session_state.feedback = (
            f"⏰ Time ran out! Correct answer: {correct}. "
            "One rope block is removed!"
        )
    else:
        selected_answer = selected
        is_correct = (
            str(selected).strip().casefold()
            == str(correct).strip().casefold()
        )

        if is_correct:
            st.session_state.score += 10
            st.session_state.rope_level = min(
                ROPE_MAX, st.session_state.rope_level + 1
            )
            st.session_state.feedback = (
                "Correct! The rope gains one block!"
            )
        else:
            st.session_state.rope_level = max(
                0, st.session_state.rope_level - 1
            )
            st.session_state.feedback = (
                f"Incorrect. Correct answer: {correct}. "
                "One rope block is removed!"
            )

    st.session_state.answers.append({
        "question": get_question_text(q),
        "selected": selected_answer,
        "correct": correct,
        "is_correct": is_correct,
        "explanation": get_explanation(q)
    })

    st.session_state.answered = True


def next_question():
    if st.session_state.current + 1 >= len(
        st.session_state.game_questions
    ):
        st.session_state.game_over = True
        st.session_state.won = (
            st.session_state.rope_level >= MIN_RESCUE_LEVEL
        )

        record_leaderboard_score()

    else:
        st.session_state.current += 1
        st.session_state.started_at = time.time()

    st.session_state.feedback = ""
    st.session_state.answered = False


def reset_to_home():
    st.session_state.started = False
    st.session_state.game_over = False
    st.session_state.won = False
    st.session_state.answered = False
    st.session_state.started_at = 0.0


# ---------------------------------------------------------
# MAIN PAGE
# ---------------------------------------------------------
st.title("🧗 Cliffside Rescue")
st.caption("One quiz. One rope. One friend to save.")

st.info(
    "🎯 **Minimum rescue criteria:** Finish all questions with a rope "
    "level of at least **8/10** to rescue your friend. Correct answers "
    "add one block; wrong answers remove one block."
)


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
if not st.session_state.started:
    st.markdown("---")
    st.markdown(
        "<h2 style='text-align:center;'>Ready for the rescue mission?</h2>"
        "<p style='text-align:center;'>Choose your challenge and see "
        "if you can save your friend!</p>",
        unsafe_allow_html=True
    )

    # NEW: Show total question count and counts by difficulty.
    question_counts = get_question_counts()

    st.markdown("### 📚 Question Bank Overview")
    total_col, easy_count_col, medium_count_col, hard_count_col = (
        st.columns(4, gap="medium")
    )

    with total_col:
        st.metric("Total Questions", len(questions))

    with easy_count_col:
        st.metric("🟢 Easy", question_counts["Easy"])

    with medium_count_col:
        st.metric("🟡 Medium", question_counts["Medium"])

    with hard_count_col:
        st.metric("🔴 Hard", question_counts["Hard"])

    # NEW: View all questions in a collapsed dropdown.
    display_all_questions()

    st.markdown("---")

    st.markdown("### 👤 Player details")
    st.session_state.player_name = st.text_input(
        "What should we call you?",
        value=st.session_state.player_name,
        placeholder="Enter your name"
    ).strip()

    st.markdown("### 🎮 Choose your difficulty")
    st.caption("You must select one level before starting.")

    easy_col, medium_col, hard_col = st.columns(3, gap="medium")

    with easy_col:
        with st.container(border=True):
            st.markdown(f"## 🟢 Easy ({question_counts['Easy']})")
            st.caption("A gentle start")
            st.write("Build confidence with easier questions.")

            if st.session_state.difficulty == "Easy":
                st.success("✓ Selected")

            if st.button(
                "Choose Easy",
                key="choose_easy",
                use_container_width=True
            ):
                st.session_state.difficulty = "Easy"
                st.session_state.difficulty_selected = True
                st.rerun()

    with medium_col:
        with st.container(border=True):
            st.markdown(f"## 🟡 Medium ({question_counts['Medium']})")
            st.caption("A balanced challenge")
            st.write("Test your knowledge with moderate questions.")

            if st.session_state.difficulty == "Medium":
                st.success("✓ Selected")

            if st.button(
                "Choose Medium",
                key="choose_medium",
                use_container_width=True
            ):
                st.session_state.difficulty = "Medium"
                st.session_state.difficulty_selected = True
                st.rerun()

    with hard_col:
        with st.container(border=True):
            st.markdown(f"## 🔴 Hard ({question_counts['Hard']})")
            st.caption("Ready for a challenge?")
            st.write("Take on the toughest questions.")

            if st.session_state.difficulty == "Hard":
                st.success("✓ Selected")

            if st.button(
                "Choose Hard",
                key="choose_hard",
                use_container_width=True
            ):
                st.session_state.difficulty = "Hard"
                st.session_state.difficulty_selected = True
                st.rerun()

    st.markdown("---")

    if st.session_state.difficulty_selected:
        st.markdown(
            f"<p style='text-align:center; font-size:17px;'>"
            f"Selected challenge: "
            f"<b>{html.escape(st.session_state.difficulty)}</b></p>",
            unsafe_allow_html=True
        )
    else:
        st.warning("Please choose a difficulty level.")

    if st.button(
        "🧗 START RESCUE",
        type="primary",
        use_container_width=True
    ):
        if not st.session_state.player_name:
            st.error("Please enter your name before starting!")
        elif not st.session_state.difficulty_selected:
            st.error("Please choose Easy, Medium, or Hard first!")
        elif not questions:
            st.error("No questions found in questions.py.")
        else:
            start_game()
            st.rerun()

    # Leaderboard on the main page.
    display_leaderboard()


# ---------------------------------------------------------
# GAME PAGE
# ---------------------------------------------------------
else:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        if st.session_state.game_over and st.session_state.won:
            heading = "🎉 RESCUE COMPLETE!"
        else:
            heading = "RESCUE IN PROGRESS"

        st.markdown(
            f'<div class="scene-title">{heading}</div>',
            unsafe_allow_html=True
        )

        draw_scene(
            st.session_state.rope_level,
            won=st.session_state.game_over and st.session_state.won
        )

    with right:
        st.subheader(f"Player: {st.session_state.player_name}")

        total = len(st.session_state.game_questions)

        progress = (
            1.0 if st.session_state.game_over
            else st.session_state.current / max(1, total)
        )
        st.progress(min(1.0, progress))

        st.write(
            f"**Question:** "
            f"{min(st.session_state.current + 1, total)} / {total}"
        )

        st.metric("Score", st.session_state.score)
        st.metric("Rope level", f"{st.session_state.rope_level}/10")

        if st.session_state.game_over:
            if st.session_state.won:
                st.header("🎉 Rescue successful!")
                st.success(
                    "You saved your friend! Both of you are safely "
                    "standing together at the top of the cliff!"
                )
            else:
                st.header("🏁 Mission finished!")
                st.warning(
                    "The rescue was not successful this time. "
                    "Try again and aim for a rope level of at least 8."
                )

            st.write(f"Final score: **{st.session_state.score}**")
            st.subheader("Answer review")

            for i, item in enumerate(st.session_state.answers, 1):
                st.write(f"**{i}. {item['question']}**")
                st.write(f"Your answer: {item['selected']}")
                st.write(f"Correct answer: {item['correct']}")

                st.write(
                    "✅ Correct" if item["is_correct"]
                    else "❌ Incorrect"
                )

                if item["explanation"]:
                    st.caption(item["explanation"])

            if st.button(
                "Play Again",
                type="primary",
                use_container_width=True
            ):
                reset_to_home()
                st.rerun()

        else:
            q = st.session_state.game_questions[
                st.session_state.current
            ]

            st.markdown(f"### {get_question_text(q)}")
            options = get_options(q)

            # TIMER: visible countdown for each question
            if not st.session_state.answered:
                elapsed = time.time() - st.session_state.started_at
                remaining = max(0, TIME_LIMIT - int(elapsed))

                if remaining <= 0:
                    answer_question(None, timed_out=True)
                    st.rerun()

                st_autorefresh(
                    interval=1000,
                    limit=TIME_LIMIT + 2,
                    key=(
                        f"timer_{st.session_state.game_id}_"
                        f"{st.session_state.current}"
                    )
                )

                st.markdown(f"### ⏱️ {remaining} seconds remaining")
                st.progress(remaining / TIME_LIMIT)

                if remaining <= 10:
                    st.warning("Hurry up! Time is running out!")

            if not options:
                st.error(
                    "This question has no options. Check questions.py."
                )

            elif not st.session_state.answered:
                choice_key = (
                    f"choice_{st.session_state.game_id}_"
                    f"{st.session_state.current}"
                )

                choice = st.radio(
                    "Select your answer:",
                    options,
                    index=None,
                    key=choice_key
                )

                if st.button(
                    "Submit Answer",
                    type="primary",
                    use_container_width=True
                ):
                    if choice is None:
                        st.warning(
                            "Please select an answer before submitting."
                        )
                    else:
                        answer_question(choice)
                        st.rerun()

            else:
                if st.session_state.feedback.startswith("Correct"):
                    st.success(st.session_state.feedback)
                elif "Time ran out" in st.session_state.feedback:
                    st.warning(st.session_state.feedback)
                else:
                    st.error(st.session_state.feedback)

                if st.button(
                    "Next Question →",
                    type="primary",
                    use_container_width=True
                ):
                    next_question()
                    st.rerun()

            if st.button("Restart Game", use_container_width=True):
                reset_to_home()
                st.rerun()
