"""
Stage 6: Actionable Feedback Generation
Uses Claude API to convert analysis into coaching advice.
"""

import anthropic

from peakflow.config import settings
from peakflow.models.schemas import DeviationAnalysis, ContextResult, FeedbackResult


FEEDBACK_PROMPT = """You are an experienced surf coach giving feedback on a bottom turn,use the powersurf(ROB MACHADO) metodology for learning with their drills.

CONTEXT:
- Surfer stance: {stance}
- Direction: {direction}
- Style match: {style_cluster}

ANALYSIS DATA:
{analysis_json}

SURF TERMINOLOGY:
- "compress" = bend knees to lower center of gravity
- "drive through" = maintain rail pressure through the turn
- "trailing arm" = back arm (away from wave)
- "leading arm" = front arm (toward wave)
- "back knee" = knee of the back foot (power leg)
- "rail" = edge of the surfboard

Generate feedback with EXACTLY this structure:

**What to Fix:** [One specific issue, 1-2 sentences. Be direct about what's wrong.]

**Why It Matters:** [One sentence on why this affects their surfing]

**Dry-Land Drill:** [One specific exercise they can practice at home, with reps/duration]

**In-Water Cue:** [A simple phrase to think while surfing, max 5 words]

Keep it encouraging but direct. Use surf terminology. Focus on the PRIMARY error only.
"""


class FeedbackGenerator:
    """Generates coaching feedback from analysis using Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(
        self,
        deviation: DeviationAnalysis,
        context: ContextResult,
        style_cluster: str = "balanced",
    ) -> FeedbackResult:
        """Generate 4-part coaching feedback from analysis."""

        # Format analysis for prompt
        analysis_json = {
            "primary_error": deviation.primary_error,
            "primary_error_description": deviation.primary_error_description,
            "severity": f"{deviation.severity:.0%}",
            "phase": deviation.phase.value,
            "timing": (
                f"{'early' if deviation.timing_offset_ms < 0 else 'late'} "
                f"by {abs(deviation.timing_offset_ms):.0f}ms"
            ),
            "joint_deviations": [
                {
                    "joint": jd.joint_name,
                    "deviation": f"{jd.max_deviation:.1f}°",
                    "phase": jd.max_deviation_phase.value,
                }
                for jd in deviation.joint_deviations[:3]  # Top 3 only
            ],
        }

        prompt = FEEDBACK_PROMPT.format(
            stance=context.stance.value,
            direction=context.direction.value,
            style_cluster=style_cluster,
            analysis_json=analysis_json,
        )

        response = self.client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse structured response
        text = response.content[0].text

        # Extract sections (simple parsing)
        sections = self._parse_sections(text)

        return FeedbackResult(
            what_to_fix=sections.get("what to fix", ""),
            why_it_matters=sections.get("why it matters", ""),
            dry_land_drill=sections.get("dry-land drill", ""),
            in_water_cue=sections.get("in-water cue", ""),
        )

    def _parse_sections(self, text: str) -> dict[str, str]:
        """Parse markdown sections from LLM response."""
        sections = {}
        current_section = None
        current_content = []

        for line in text.split("\n"):
            if line.startswith("**") and ":**" in line:
                # Save previous section
                if current_section:
                    sections[current_section] = " ".join(current_content).strip()

                # Parse new section header
                header_part = line.split(":**")[0].replace("**", "").strip().lower()
                current_section = header_part

                # Get content after the header on the same line
                content_after = line.split(":**")[1].strip() if ":**" in line else ""
                current_content = [content_after] if content_after else []
            elif current_section:
                current_content.append(line.strip())

        # Save last section
        if current_section:
            sections[current_section] = " ".join(current_content).strip()

        return sections

    def generate_fallback(
        self,
        deviation: DeviationAnalysis,
        context: ContextResult,
    ) -> FeedbackResult:
        """Generate basic feedback without LLM when API is unavailable."""

        error_feedback = {
            "knee_flexion_back": {
                "what_to_fix": (
                    "Your back knee isn't compressing enough through the turn. "
                    "You need to drive that back knee toward the deck."
                ),
                "why_it_matters": (
                    "Without back knee compression, you lose power and rail engagement."
                ),
                "drill": (
                    "Wall squats with focus on back leg: 3 sets of 30 seconds, "
                    "really driving back knee down."
                ),
                "cue": "Knee to deck",
            },
            "knee_flexion_front": {
                "what_to_fix": (
                    "Your front knee is too stiff through the turn. "
                    "Bend that front knee to lower your center of gravity."
                ),
                "why_it_matters": (
                    "Stiff front leg raises your stance and reduces control."
                ),
                "drill": (
                    "Single-leg quarter squats on front leg: 3 sets of 10 reps each side."
                ),
                "cue": "Soft front knee",
            },
            "torso_lean": {
                "what_to_fix": (
                    "Your torso isn't leaning into the turn enough. "
                    "Commit your upper body to follow the rail."
                ),
                "why_it_matters": (
                    "Upright torso means less rail pressure and weaker turns."
                ),
                "drill": (
                    "Standing rotation stretches with medicine ball: "
                    "3 sets of 15 twists each direction."
                ),
                "cue": "Shoulder to wave",
            },
            "compression_index": {
                "what_to_fix": (
                    "Your overall stance is too tall through the turn. "
                    "Get low and compress your whole body."
                ),
                "why_it_matters": (
                    "Standing tall means less stability and power through the turn."
                ),
                "drill": (
                    "Deep squat holds in surf stance: 3 sets of 45 seconds."
                ),
                "cue": "Get low, stay low",
            },
        }

        # Get feedback for primary error
        error_type = deviation.primary_error
        feedback_data = error_feedback.get(
            error_type,
            {
                "what_to_fix": f"Focus on improving your {error_type.replace('_', ' ')}.",
                "why_it_matters": "This affects your overall turn quality.",
                "drill": "Practice basic surf stance holds: 3 sets of 30 seconds.",
                "cue": "Stay balanced",
            },
        )

        return FeedbackResult(
            what_to_fix=feedback_data["what_to_fix"],
            why_it_matters=feedback_data["why_it_matters"],
            dry_land_drill=feedback_data["drill"],
            in_water_cue=feedback_data["cue"],
        )
