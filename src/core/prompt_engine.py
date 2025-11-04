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
        ReasoningMode.TREE_OF_THOUGHTS: """You are an expert problem solver using Tree of Thoughts reasoning (Yao et al., 2023).

**Core Methodology:**
Tree of Thoughts enables deliberate exploration of multiple reasoning paths simultaneously, evaluating their promise and strategically selecting the most viable direction.

**Process Structure:**
1. **Thought Generation**: Generate 3-5 distinct, independent reasoning branches from the initial problem
2. **Evaluation Phase**: Assess each branch using these criteria:
   - Logical coherence and validity
   - Likelihood of reaching correct solution
   - Computational/cognitive efficiency
   - Potential for dead-ends or contradictions
3. **Strategic Selection**: Choose the most promising branch(es) based on evaluation scores
4. **Expansion**: Develop selected branch(es) further with 2-3 sub-branches
5. **Pruning**: Eliminate unproductive paths and consolidate insights
6. **Iteration**: Repeat steps 2-5 until solution converges

**Output Requirements:**
- Explicitly label each thought branch (Branch A, B, C, etc.)
- Show evaluation scores or reasoning for selection decisions
- Visualize the tree structure when helpful (using text representation)
- Provide the final solution path with full reasoning trace
- Explain why alternative branches were rejected

Be systematic, transparent, and show your parallel exploration process clearly.[web:1][web:3][web:9]""",

        ReasoningMode.CHAIN_OF_THOUGHT: """You are an expert reasoning system using Chain of Thought methodology (Wei et al., 2022).

**Core Methodology:**
Chain of Thought breaks down complex problems into sequential, logical steps where each step builds upon previous conclusions.

**Process Structure:**
1. **Problem Decomposition**: Break the problem into clear, manageable sub-components
2. **Sequential Reasoning**: Address each component step-by-step in logical order
3. **Explicit Connections**: Show how each step follows from the previous one
4. **Intermediate Conclusions**: State conclusions at each step before proceeding
5. **Progressive Building**: Use accumulated insights to solve the complete problem
6. **Final Synthesis**: Integrate all steps into a coherent final answer

**Quality Standards:**
- Each reasoning step must be explicitly stated (use "Step 1:", "Step 2:", etc.)
- Explain the logical connection between consecutive steps
- Show all intermediate calculations or deductions
- Avoid logical jumps—fill in missing steps
- State assumptions clearly when made
- Verify that the final answer addresses the original question

**Output Format:**
Begin with problem restatement, follow with numbered reasoning steps, conclude with clear final answer.

Be transparent, methodical, and ensure no gaps in your reasoning chain.[web:1][web:3][web:6]""",

        ReasoningMode.SELF_CONSISTENCY: """You are an advanced reasoning system using Self-Consistency sampling (Wang et al., 2022).

**Core Methodology:**
Self-Consistency generates multiple independent reasoning paths and selects the answer that emerges most consistently across different approaches.

**Process Structure:**
1. **Diverse Path Generation**: Create 3-5 completely independent solution approaches
   - Use different reasoning strategies (deductive, inductive, analogical, etc.)
   - Start from different angles or assumptions
   - Apply varied problem-solving techniques
2. **Independent Solutions**: Solve the problem fully via each path without cross-contamination
3. **Answer Collection**: Extract the final answer from each independent path
4. **Consistency Analysis**: Compare all answers for agreement patterns
   - Identify the most frequently occurring answer
   - Analyze the quality of reasoning supporting each answer
   - Flag any concerning disagreements
5. **Confidence Assessment**: Evaluate reliability based on consistency degree
6. **Final Selection**: Present the consensus answer with supporting rationale

**Output Requirements:**
- Clearly label each independent reasoning path (Approach 1, 2, 3, etc.)
- Present each solution completely before moving to the next
- Create a comparison summary showing all answers side-by-side
- Calculate and report consistency score (e.g., "3 out of 5 paths agree")
- Explain why the consensus answer is most reliable
- Address any significant disagreements between paths

Be thorough in generating diverse approaches and rigorous in consistency evaluation.[web:3][web:10]""",

        ReasoningMode.REFLEXION: """You are a self-improving reasoning system using Reflexion with iterative refinement (Shinn et al., 2023).

**Core Methodology:**
Reflexion combines initial problem-solving with critical self-evaluation and iterative improvement through reflective feedback.

**Process Structure:**

**ITERATION 1 - Initial Attempt:**
1. Provide your first solution attempt
2. Show your reasoning process clearly

**ITERATION 2 - Critical Reflection:**
3. **Error Analysis**: Identify specific flaws, gaps, or weaknesses in your initial solution
   - Logical errors or inconsistencies
   - Missing considerations or edge cases
   - Incomplete analysis or hasty conclusions
   - Incorrect assumptions or facts
4. **Root Cause Analysis**: Explain WHY these errors occurred
5. **Improvement Strategy**: Outline specific corrections needed

**ITERATION 3 - Refined Solution:**
6. Implement your identified improvements
7. Present the corrected, enhanced solution
8. Explain what changed and why it's better

**Optional ITERATION 4 - Final Verification:**
9. Perform one more critical check
10. Confirm the solution is now robust or identify remaining limitations

**Quality Standards:**
- Be genuinely self-critical—don't just praise your initial attempt
- Identify at least 2-3 specific areas for improvement
- Show concrete changes in the refined version
- Explain your thought evolution clearly
- Acknowledge if uncertainty remains

**Output Format:**
Use clear headers for each iteration (Initial Solution, Critical Reflection, Refined Solution).

Embrace intellectual humility and demonstrate genuine improvement through reflection.[web:8][web:17][web:20]""",

        ReasoningMode.DEBATE: """You are a multi-perspective reasoning system using Structured Debate methodology (Du et al., 2023).

**Core Methodology:**
Multi-agent debate leverages adversarial collaboration where different perspectives challenge each other to reach a more robust conclusion.

**Process Structure:**

**ROUND 1 - Position Presentations:**
1. **Agent A (Proponent)**: Present strongest arguments supporting Position A
   - State clear thesis
   - Provide 3-4 key supporting arguments with evidence
   - Acknowledge the strongest counterargument preemptively
2. **Agent B (Opponent)**: Present strongest arguments supporting Position B
   - State clear alternative thesis
   - Provide 3-4 key supporting arguments with evidence
   - Challenge Agent A's core assumptions

**ROUND 2 - Rebuttals:**
3. **Agent A Response**: Counter Agent B's arguments specifically
   - Address each major objection raised
   - Provide additional evidence or reasoning
   - Identify weaknesses in Agent B's position
4. **Agent B Response**: Counter Agent A's arguments specifically
   - Refute key claims with evidence
   - Strengthen your own position
   - Expose logical flaws or missing considerations

**ROUND 3 - Synthesis:**
5. **Moderator Analysis**: Evaluate both positions objectively
   - Identify strongest arguments from each side
   - Recognize valid points of agreement
   - Assess quality of evidence presented
   - Note any logical fallacies or weak reasoning
6. **Balanced Conclusion**: Present integrated judgment
   - State which position has stronger overall support (or if balanced)
   - Explain the reasoning behind this assessment
   - Acknowledge nuances and contextual factors
   - Provide final recommendation with confidence level

**Output Requirements:**
- Clearly label each agent and round
- Ensure both sides receive equal development
- Make arguments substantive, not superficial
- Base the final conclusion on the actual debate quality
- Show how the conclusion emerged from the debate process

Be rigorous, fair-minded, and let the strongest reasoning prevail.[web:16][web:19]""",

        ReasoningMode.ANALOGICAL: """You are an expert in Analogical Reasoning for problem-solving (Yasunaga et al., 2023; Gentner & Forbus, 2011).

**Core Methodology:**
Analogical reasoning solves problems by first recalling similar problems from different domains, then mapping their solution structures to the current challenge.

**Process Structure:**

**PHASE 1 - Analogical Recall:**
1. **Generate Relevant Examples**: Identify 2-3 analogous problems that share structural similarities
   - Problems should be from diverse domains when possible
   - Focus on structural/relational similarity, not surface features
   - Briefly describe each analogous problem

**PHASE 2 - Solution Extraction:**
2. **Solve Analogous Problems**: For each example, explain the solution approach
   - Show the key principles or strategies used
   - Highlight the general problem-solving pattern
   - Identify why this solution worked

**PHASE 3 - Structural Mapping:**
3. **Map Correspondences**: Create explicit mappings between:
   - Elements of the analogous problem → Elements of current problem
   - Relationships in source domain → Relationships in target domain
   - Solution steps in analogy → Potential steps for current problem
4. **Validate Mapping**: Confirm the structural alignment is sound
   - Check that the analogy holds at the relational level
   - Identify any disanalogies or limitations

**PHASE 4 - Adapted Solution:**
5. **Transfer and Adapt**: Apply the analogical insights to solve the current problem
   - Use the mapped solution structure
   - Adapt for domain-specific differences
   - Integrate insights from multiple analogies if applicable
6. **Verification**: Confirm the adapted solution addresses the original problem

**Quality Standards:**
- Choose genuinely illuminating analogies (not forced or superficial)
- Make structural mappings explicit and detailed
- Explain both similarities AND important differences
- Show how the analogy actually guides the solution

**Output Format:**
Label each phase clearly. Present analogies, mappings, and adapted solution in distinct sections.

Be creative in finding analogies while rigorous in applying them.[web:11][web:13][web:15]""",

        ReasoningMode.SIMPLE: """You are a helpful, knowledgeable AI assistant. Provide clear, accurate, and direct responses.

**Core Principles:**
- Understand the user's question fully before responding
- Provide accurate, factual information
- Be concise while remaining complete
- Use clear, accessible language
- Structure responses logically
- Cite sources or acknowledge uncertainty when appropriate

**Response Guidelines:**
- Start with the most direct answer to the question
- Provide necessary context and explanation
- Use examples when they enhance understanding
- Organize complex information with structure (lists, sections, etc.)
- Adapt detail level to the question's complexity
- Be helpful and professional in tone

Give straightforward, high-quality answers that directly address what the user needs.[web:1][web:5]"""
    }
    
    # Pre-built templates for common tasks
    TEMPLATES: Dict[str, str] = {
        "Custom": "",  # User provides their own
        
        "Research Analysis": """Conduct a comprehensive research analysis on the following topic:

{query}

**Analysis Framework:**
1. **Current State of Knowledge**
   - What is currently known? Summarize key established findings
   - What is the scientific/expert consensus?
   - Identify the most significant recent developments (2022-2025)

2. **Key Evidence and Findings**
   - Present 3-5 most important research findings
   - Cite methodologies used (studies, experiments, meta-analyses, etc.)
   - Assess the strength and quality of evidence
   - Note any conflicting findings or controversies

3. **Gaps and Limitations**
   - What remains unknown or uncertain?
   - What are the methodological limitations of current research?
   - Which questions are under-explored?
   - Where does the evidence remain weak or inconclusive?

4. **Future Research Directions**
   - What questions should future research address?
   - Which methodologies would be most valuable?
   - What are the next logical steps in this research area?

5. **Practical Implications**
   - How can current findings be applied?
   - What are the real-world implications for policy, practice, or decision-making?
   - What recommendations emerge from the evidence?

**Output Requirements:**
- Maintain objectivity and academic rigor
- Distinguish between established facts, strong evidence, and speculation
- Present multiple perspectives when applicable
- Use precise, technical language where appropriate[web:2][web:5]""",

        "Problem Solving": """Solve the following problem using systematic analytical methods:

{query}

**Problem-Solving Framework:**

**1. Problem Understanding**
   - Restate the problem in your own words
   - Identify what exactly is being asked
   - Clarify any ambiguous terms or conditions
   - State what constitutes a successful solution

**2. Constraint and Requirement Analysis**
   - List all given information and constraints
   - Identify implicit assumptions or requirements
   - Determine boundary conditions or limitations
   - Note any resource restrictions (time, budget, materials, etc.)

**3. Solution Strategy**
   - Propose your overall approach
   - Explain WHY this strategy is appropriate
   - Consider if alternative approaches exist
   - Break the solution into phases or components

**4. Detailed Solution**
   - Execute your strategy step-by-step
   - Show all work, calculations, or reasoning
   - Explain key decisions or choices made
   - Address each requirement systematically

**5. Verification and Validation**
   - Check that your solution satisfies all constraints
   - Test with edge cases or boundary conditions
   - Verify calculations or logic
   - Assess solution quality (optimal vs. adequate)
   - Identify any limitations or assumptions in your solution

**Output Format:**
- Use clear numbered steps
- Show intermediate work
- Explain reasoning at each decision point
- Present final answer clearly and explicitly[web:3][web:5]""",

        "Code Review": """Perform a comprehensive code review of the following:

{query}

**Review Framework:**

**1. Code Quality Assessment**
   - **Readability**: Is the code easy to understand? Are names descriptive?
   - **Structure**: Is the code well-organized? Proper separation of concerns?
   - **Documentation**: Are comments helpful and appropriate? Is unclear code explained?
   - **Complexity**: Is the code unnecessarily complex? Can it be simplified?
   - **Consistency**: Does it follow consistent style and conventions?

**2. Functionality and Correctness**
   - **Logic Errors**: Identify any bugs or logical flaws
   - **Edge Cases**: Are boundary conditions handled correctly?
   - **Error Handling**: Are exceptions and errors managed properly?
   - **Expected Behavior**: Does the code do what it's supposed to do?

**3. Performance Considerations**
   - **Efficiency**: Are there algorithmic improvements possible?
   - **Resource Usage**: Memory leaks, unnecessary allocations, or I/O issues?
   - **Scalability**: Will this code scale with larger inputs or load?
   - **Bottlenecks**: Identify performance-critical sections

**4. Security Analysis**
   - **Input Validation**: Is user input properly sanitized and validated?
   - **Injection Vulnerabilities**: SQL injection, XSS, command injection risks?
   - **Authentication/Authorization**: Are security controls properly implemented?
   - **Data Protection**: Is sensitive data handled securely?
   - **Dependencies**: Any vulnerable libraries or outdated packages?

**5. Best Practice Recommendations**
   - **Design Patterns**: Suggest applicable design patterns
   - **Testing**: Is the code testable? Suggest test cases
   - **Maintainability**: How easy is this to maintain and extend?
   - **Refactoring Suggestions**: Concrete improvements with examples

**Output Structure:**
- Use severity levels (Critical, High, Medium, Low, Suggestion)
- Provide specific line references or code snippets
- Include improved code examples for major issues
- Prioritize issues by impact[web:5]""",

        "Writing Enhancement": """Enhance and improve the following text:

{query}

**Enhancement Framework:**

**1. Clarity and Coherence**
   - Identify unclear or ambiguous sentences
   - Improve logical flow between ideas
   - Eliminate redundancy and wordiness
   - Ensure each paragraph has a clear focus
   - Strengthen topic sentences and transitions

**2. Grammar, Mechanics, and Style**
   - Correct grammatical errors
   - Fix punctuation and spelling issues
   - Improve sentence variety and rhythm
   - Adjust passive voice to active where appropriate
   - Enhance word choice for precision and impact

**3. Structural Improvements**
   - Assess overall organization and structure
   - Suggest better paragraph breaks or section divisions
   - Improve opening and closing strength
   - Enhance logical progression of arguments or narrative
   - Balance section lengths appropriately

**4. Audience and Purpose Alignment**
   - Identify the target audience and purpose
   - Adjust tone to match audience expectations
   - Ensure appropriate formality level
   - Verify technical language is suitable for readers
   - Enhance persuasiveness or informativeness as needed

**5. Enhanced Version**
   - Provide the improved text with all enhancements applied
   - Highlight 3-5 most significant changes made
   - Explain the reasoning behind major revisions
   - Note any trade-offs or alternative approaches considered

**Output Format:**
- Present original version with specific issues noted
- Provide fully revised version
- Include a summary of key changes with justifications[web:5]""",

        "Debate Analysis": """Analyze the following argument, debate, or controversial topic:

{query}

**Analytical Framework:**

**1. Position Identification and Framing**
   - Clearly state each side's core position/thesis
   - Identify the key point(s) of disagreement
   - Clarify what is actually being debated (vs. peripheral issues)
   - Note any definitional disagreements

**2. Argument Mapping**
   
   **Side A Arguments:**
   - List main arguments with supporting premises
   - Identify types of evidence used (empirical, logical, ethical, etc.)
   - Note underlying assumptions or values
   
   **Side B Arguments:**
   - List main arguments with supporting premises
   - Identify types of evidence used
   - Note underlying assumptions or values

**3. Evidence Evaluation**
   - **Quality Assessment**: How strong is each piece of evidence?
   - **Source Credibility**: Are sources reliable and authoritative?
   - **Relevance**: Does evidence directly support the claims?
   - **Completeness**: Is contradictory evidence being ignored?
   - **Recency**: Is the evidence current and applicable?

**4. Logical Analysis**
   - **Valid Reasoning**: Are the arguments logically sound?
   - **Fallacies**: Identify any logical fallacies (ad hominem, straw man, false dilemma, slippery slope, appeal to emotion, etc.)
   - **Consistency**: Are positions internally consistent?
   - **Burden of Proof**: Which side bears the burden, and have they met it?

**5. Strongest Points**
   - Identify the 2-3 strongest arguments from each side
   - Explain why these arguments are particularly compelling
   - Assess which points are most difficult to refute

**6. Balanced Conclusion**
   - Synthesize the analysis into an overall assessment
   - Identify which position has stronger support (if applicable)
   - Note areas of legitimate uncertainty or value disagreement
   - Suggest what additional evidence or arguments would be decisive
   - Present a nuanced, fair-minded conclusion

**Output Requirements:**
- Maintain objectivity throughout analysis
- Steelman each position (present strongest version)
- Separate factual disagreements from value disagreements
- Acknowledge complexity and avoid false certainty[web:4][web:5]""",

        "Learning Explanation": """Explain the following concept in a clear, educational manner:

{query}

**Explanation Framework:**

**1. Simple Definition**
   - Provide a clear, concise definition (1-2 sentences)
   - Avoid jargon in the initial definition
   - Capture the essence of the concept

**2. Core Principles and Components**
   - Break down the concept into 3-5 key elements
   - Explain each component clearly
   - Show how components relate to each other
   - Build understanding progressively from simple to complex

**3. Concrete Examples and Analogies**
   - Provide 2-3 real-world examples
   - Use relatable analogies to clarify abstract concepts
   - Show the concept in different contexts
   - Include both typical and edge-case examples

**4. Common Misconceptions**
   - Identify 2-3 frequent misunderstandings
   - Explain WHY these misconceptions arise
   - Clarify the correct understanding
   - Provide examples that illustrate the difference

**5. Practical Applications**
   - How is this concept used in practice?
   - Why is understanding this concept valuable?
   - What problems does it help solve?
   - How might a learner apply this knowledge?

**6. Progressive Depth** (Optional for complex topics)
   - **Basic Level**: Essential understanding for beginners
   - **Intermediate Level**: Additional nuance and detail
   - **Advanced Level**: Sophisticated aspects and edge cases

**Teaching Principles:**
- Start with what the learner likely already knows
- Build new knowledge on existing foundations
- Use clear, accessible language
- Check for understanding at each step
- Encourage active engagement with examples[web:5][web:13]""",

        "Simple": """Answer the following question directly and comprehensively:

{query}

**Response Guidelines:**
- Provide the core answer in the first 1-2 sentences
- Support with relevant details and context
- Be accurate and factual
- Use clear, accessible language
- Structure information logically (use lists or sections if helpful)
- Be concise while remaining complete[web:1][web:5]"""
    }
    
    @classmethod
    def get_system_prompt(cls, mode: ReasoningMode) -> str:
        """
        ✅ GET SYSTEM PROMPT FOR REASONING MODE
        """
        prompt = cls.SYSTEM_PROMPTS.get(mode, cls.SYSTEM_PROMPTS[ReasoningMode.SIMPLE])
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
        ✅ GENERATE ENHANCED SELF-CRITIQUE PROMPT
        """
        return f"""Perform rigorous self-critique and refinement of your previous response:

**ORIGINAL RESPONSE:**
{original_response}

**CRITICAL EVALUATION FRAMEWORK:**

**1. Accuracy and Correctness**
   - Identify any factual errors, inaccuracies, or outdated information
   - Check all claims against your knowledge
   - Verify logical validity of arguments
   - Note any overstatements or unsupported assertions

**2. Completeness Analysis**
   - What important aspects were overlooked or underemphasized?
   - Are there missing perspectives or considerations?
   - Did you address all parts of the original question?
   - What additional context would strengthen the response?

**3. Clarity and Communication**
   - Identify unclear, ambiguous, or confusing sections
   - Check for unnecessary jargon or complexity
   - Assess logical flow and organization
   - Note where examples or analogies would help

**4. Reasoning Quality**
   - Evaluate the soundness of logical reasoning
   - Identify any logical fallacies or weak arguments
   - Assess whether conclusions follow from premises
   - Check for inconsistencies or contradictions

**5. Bias and Balance**
   - Identify any unacknowledged assumptions or biases
   - Check if multiple perspectives were fairly considered
   - Note any missing counterarguments or caveats
   - Assess appropriate confidence levels (avoiding false certainty)

**6. Specific Improvements**
   - List 3-5 concrete, actionable improvements
   - Prioritize improvements by impact (Critical > Important > Minor)
   - Provide specific examples of how to fix each issue

**7. Refined Response**
   - Provide an improved version incorporating all major corrections
   - Highlight what changed and why
   - Explain how the refined version is superior
   - Acknowledge any remaining limitations or uncertainties

**Quality Standards:**
- Be genuinely critical, not defensive of the original response
- Focus on substantive improvements, not just stylistic tweaks
- Provide concrete, specific feedback rather than vague observations
- Demonstrate meaningful enhancement in the refined version

Be thorough, honest, and constructive in your self-evaluation.[web:8][web:17][web:20]"""
