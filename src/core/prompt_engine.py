"""
Centralized prompt management and template system
"""
from typing import Dict, List, Optional
from src.config.constants import ReasoningMode
from src.utils.logger import logger


class PromptEngine:
    """
    📝 CENTRALIZED PROMPT MANAGEMENT
    Research-backed prompt templates for different reasoning modes
    """
    
    # System prompts for each reasoning mode
    SYSTEM_PROMPTS: Dict[ReasoningMode, str] = {
        ReasoningMode.TREE_OF_THOUGHTS: """You are an advanced AI using Tree of Thoughts reasoning (Yao et al., 2023).

**Instructions:**
1. Generate 3 distinct reasoning paths
2. Evaluate each path's viability
3. Select the most promising path
4. Expand and refine iteratively
5. Present the best solution with reasoning trace

Be systematic, thorough, and show your branching logic.""",

        ReasoningMode.CHAIN_OF_THOUGHT: """You are an advanced AI using Chain of Thought reasoning (Wei et al., 2022).

**Instructions:**
1. Break down the problem into clear steps
2. Show explicit reasoning for each step
3. Build on previous conclusions
4. Arrive at final answer logically
5. Explain your thought process

Be clear, sequential, and transparent in your reasoning.""",

        ReasoningMode.SELF_CONSISTENCY: """You are an advanced AI using Self-Consistency sampling (Wang et al., 2022).

**Instructions:**
1. Generate 3 independent solution paths
2. Solve the problem using different approaches
3. Compare solutions for consistency
4. Identify the most reliable answer
5. Present the consensus solution

Show multiple perspectives and explain why one answer is most consistent.""",

        ReasoningMode.REFLEXION: """You are an advanced AI using Reflexion with self-correction (Shinn et al., 2023).

**Instructions:**
1. Provide initial solution
2. Critique your own reasoning
3. Identify potential errors or gaps
4. Refine and improve solution
5. Present corrected answer with reflection

Be self-critical and show your improvement process.""",

        ReasoningMode.DEBATE: """You are an advanced AI using Multi-Agent Debate (Du et al., 2023).

**Instructions:**
1. Present Perspective A with arguments
2. Present Perspective B with counterarguments
3. Debate key points of disagreement
4. Synthesize the strongest arguments
5. Conclude with balanced judgment

Show multiple viewpoints and reasoned synthesis.""",

        ReasoningMode.ANALOGICAL: """You are an advanced AI using Analogical Reasoning (Gentner & Forbus, 2011).

**Instructions:**
1. Identify similar problems or domains
2. Map structural similarities
3. Transfer solution strategies
4. Adapt to current problem context
5. Verify applicability

Draw meaningful analogies and explain transfer logic."""
    }
    
    # Pre-built templates for common tasks
    TEMPLATES: Dict[str, str] = {
        "Custom": "",  # User provides their own
        
        "Research Analysis": """Analyze the following research question or topic:

{query}

Provide:
1. Current state of knowledge
2. Key findings and evidence
3. Gaps or limitations
4. Future directions
5. Practical implications""",

        "Problem Solving": """Solve the following problem systematically:

{query}

Include:
1. Problem understanding
2. Constraints and requirements
3. Solution approach
4. Step-by-step solution
5. Verification""",

        "Code Review": """Review the following code:

{query}

Analyze:
1. Code quality and readability
2. Potential bugs or issues
3. Performance considerations
4. Best practice recommendations
5. Security concerns""",

        "Writing Enhancement": """Improve the following text:

{query}

Focus on:
1. Clarity and coherence
2. Grammar and style
3. Structural improvements
4. Audience appropriateness
5. Enhanced version""",

        "Debate Analysis": """Analyze the following argument or debate topic:

{query}

Provide:
1. Key arguments for each side
2. Evidence evaluation
3. Logical fallacies (if any)
4. Strongest points
5. Balanced conclusion""",

        "Learning Explanation": """Explain the following concept:

{query}

Include:
1. Simple definition
2. Core principles
3. Examples and analogies
4. Common misconceptions
5. Practical applications"""
    }
    
    @classmethod
    def get_system_prompt(cls, mode: ReasoningMode) -> str:
        """
        ✅ GET SYSTEM PROMPT FOR REASONING MODE
        """
        prompt = cls.SYSTEM_PROMPTS.get(mode, cls.SYSTEM_PROMPTS[ReasoningMode.CHAIN_OF_THOUGHT])
        logger.debug(f"📝 Retrieved system prompt for mode: {mode}")
        return prompt
    
    @classmethod
    def apply_template(cls, template_name: str, query: str) -> str:
        """
        ✅ APPLY PROMPT TEMPLATE
        """
        if template_name not in cls.TEMPLATES:
            logger.warning(f"⚠️ Template '{template_name}' not found, using query as-is")
            return query
        
        template = cls.TEMPLATES[template_name]
        
        if not template:  # Custom template
            return query
        
        formatted = template.format(query=query)
        logger.debug(f"📝 Applied template: {template_name}")
        return formatted
    
    @classmethod
    def build_messages(cls, 
                      query: str, 
                      mode: ReasoningMode,
                      template: str = "Custom",
                      history: Optional[List[Dict]] = None) -> List[Dict]:
        """
        ✅ BUILD MESSAGE ARRAY FOR API
        """
        messages = [
            {"role": "system", "content": cls.get_system_prompt(mode)}
        ]
        
        # Add conversation history
        if history:
            for msg in history[-10:]:  # Last 10 messages
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add current query with template
        formatted_query = cls.apply_template(template, query)
        messages.append({"role": "user", "content": formatted_query})
        
        logger.debug(f"📝 Built message array with {len(messages)} messages")
        return messages
    
    @classmethod
    def get_self_critique_prompt(cls, original_response: str) -> str:
        """
        ✅ GENERATE SELF-CRITIQUE PROMPT
        """
        return f"""Review and critique the following response:

{original_response}

**Self-Critique Instructions:**
1. Identify any factual errors or logical flaws
2. Check for completeness and clarity
3. Evaluate reasoning quality
4. Suggest specific improvements
5. Provide refined answer if needed

Be thorough and constructive in your critique."""
