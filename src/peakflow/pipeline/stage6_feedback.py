"""
Stage 6: Actionable Feedback Generation
Uses Claude API to convert analysis into coaching advice.
"""

import anthropic

from peakflow.config import settings
from peakflow.models.schemas import DeviationAnalysis, ContextResult, MatchResult, FeedbackResult


FEEDBACK_PROMPT = """You are an experienced surf coach giving feedback on a bottom turn, use the powersurf (ROB MACHADO) methodology for learning with their drills.

CONTEXT:
- Surfer stance: {stance}
- Direction: {direction}
- Style match: {style_cluster}
- Matched pro: {matched_pro}

OBSERVATIONS:
{observations}

SURF TERMINOLOGY:
- "compress" = bend knees to lower center of gravity
- "drive through" = maintain rail pressure through the turn
- "trailing arm" = back arm (away from wave)
- "leading arm" = front arm (toward wave)
- "back knee" = knee of the back foot (power leg)
- "rail" = edge of the surfboard

Generate feedback with EXACTLY this structure (6 sections):

**What We See:** [Describe the body position/movement you detect. No numbers or degrees — use surf language like "your back knee stays too straight", "upper body is opening too early". 1-2 sentences.]

**What to Fix:** [One specific correction, 1-2 sentences. Be direct about what's wrong.]

**Why It Matters:** [One sentence on why this affects their surfing]

**Pro Insight:** [How the matched pro ({matched_pro}) handles this differently, in qualitative terms. E.g. "Medina drops his back knee almost to the deck before exploding upward." 1-2 sentences.]

**Dry-Land Drill:** [One specific exercise they can practice at home, with reps/duration]

**In-Water Cue:** [A simple phrase to think while surfing, max 5 words]

Keep it encouraging but direct. Use surf terminology. Focus on the PRIMARY error only. Do NOT use any numerical measurements — describe everything qualitatively.
"""


class FeedbackGenerator:
    """Generates coaching feedback from analysis using Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    @staticmethod
    def _severity_label(severity: float) -> str:
        """Convert 0-1 severity to a qualitative label."""
        if severity < 0.25:
            return "slightly"
        if severity < 0.50:
            return "moderately"
        if severity < 0.75:
            return "significantly"
        return "very"

    @staticmethod
    def _joint_label(joint_name: str) -> str:
        """Convert joint key to readable surf-language label."""
        mapping = {
            "knee_flexion_back": "back knee",
            "knee_flexion_front": "front knee",
            "hip_flexion": "hip",
            "torso_lean": "torso lean",
            "compression_index": "overall compression",
            "arm_elevation_leading": "leading arm",
            "arm_elevation_trailing": "trailing arm",
        }
        return mapping.get(joint_name, joint_name.replace("_", " "))

    def generate(
        self,
        deviation: DeviationAnalysis,
        context: ContextResult,
        style_cluster: str = "balanced",
        match: MatchResult | None = None,
    ) -> FeedbackResult:
        """Generate 6-part coaching feedback from analysis."""

        matched_pro = (
            match.matched_references[0].surfer_name
            if match and match.matched_references
            else "the reference pro"
        )

        # Build qualitative observations instead of numerical data
        severity = self._severity_label(deviation.severity)
        observations = [
            f"Primary issue: {deviation.primary_error_description}",
            f"Severity: {severity} off from pro reference",
            f"Phase: {deviation.phase.value.replace('_', ' ')}",
        ]
        for jd in deviation.joint_deviations[:3]:
            label = self._joint_label(jd.joint_name)
            sev = self._severity_label(jd.max_deviation / 45.0)  # normalize rough
            observations.append(
                f"- {label}: {sev} off during {jd.max_deviation_phase.value.replace('_', ' ')}"
            )

        prompt = FEEDBACK_PROMPT.format(
            stance=context.stance.value,
            direction=context.direction.value,
            style_cluster=style_cluster,
            matched_pro=matched_pro,
            observations="\n".join(observations),
        )

        response = self.client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        sections = self._parse_sections(text)

        return FeedbackResult(
            what_you_are_doing=sections.get("what we see", ""),
            what_to_fix=sections.get("what to fix", ""),
            why_it_matters=sections.get("why it matters", ""),
            dry_land_drill=sections.get("dry-land drill", ""),
            in_water_cue=sections.get("in-water cue", ""),
            pro_insight=sections.get("pro insight", ""),
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
        match: MatchResult | None = None,
    ) -> FeedbackResult:
        """Generate basic feedback without LLM when API is unavailable."""

        matched_pro = (
            match.matched_references[0].surfer_name
            if match and match.matched_references
            else "the reference pro"
        )

        error_feedback = {
            "knee_flexion_back": {
                "observation": (
                    "Your back knee stays fairly straight as you enter the bottom turn "
                    "instead of dropping toward the deck."
                ),
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
                "pro_insight": (
                    f"{matched_pro} drops the back knee almost to the deck before "
                    "exploding upward, loading the board like a spring."
                ),
            },
            "knee_flexion_front": {
                "observation": (
                    "Your front leg looks rigid through the turn, keeping your "
                    "center of gravity too high."
                ),
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
                "pro_insight": (
                    f"{matched_pro} keeps a noticeably soft front knee throughout, "
                    "absorbing chop and maintaining rail contact."
                ),
            },
            "torso_lean": {
                "observation": (
                    "Your upper body stays relatively upright instead of committing "
                    "into the turn with the rail."
                ),
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
                "pro_insight": (
                    f"{matched_pro} tilts the whole torso into the wave face, "
                    "leading with the shoulder to maximize rail engagement."
                ),
            },
            "compression_index": {
                "observation": (
                    "Your overall stance is tall and extended through the turn "
                    "rather than compressed and loaded."
                ),
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
                "pro_insight": (
                    f"{matched_pro} compresses the entire body into a tight, "
                    "coiled position before releasing through the turn."
                ),
            },
        }

        error_type = deviation.primary_error
        feedback_data = error_feedback.get(
            error_type,
            {
                "observation": (
                    f"Your {error_type.replace('_', ' ')} looks off compared to "
                    "the pro reference."
                ),
                "what_to_fix": f"Focus on improving your {error_type.replace('_', ' ')}.",
                "why_it_matters": "This affects your overall turn quality.",
                "drill": "Practice basic surf stance holds: 3 sets of 30 seconds.",
                "cue": "Stay balanced",
                "pro_insight": (
                    f"{matched_pro} handles this phase with noticeably better "
                    "body positioning and timing."
                ),
            },
        )

        return FeedbackResult(
            what_you_are_doing=feedback_data["observation"],
            what_to_fix=feedback_data["what_to_fix"],
            why_it_matters=feedback_data["why_it_matters"],
            dry_land_drill=feedback_data["drill"],
            in_water_cue=feedback_data["cue"],
            pro_insight=feedback_data["pro_insight"],
        )
