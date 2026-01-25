What I like about your research:

Your ability to match Gas Town into our SDLC workflow.
Ideas of separating Rafinery (from CAB) role and adding event-driven notifications. More details would be welcome - do you think about any kind of programmatic queue or just a file treated as FIFO?

What I would consider despite your objections: tmux. I know and I like tmux, so from my perspective the technology is not diffcult - please explain where do you see the complexity.
Multiple runtime support: definitely agree with you. I have Claude Code with access to its models Haiku (simpler, faster), Sonnet (middle point, slightly more expensive) and Opus (the most intelligent, slightly more expensive than Sonnet, but definitely with smaller pool of tokens to burn:

  Current session                                                                                                                                                                                   
                                                     0% used                                                                                                                                        
  Resets 10pm (Europe/Warsaw)                                                                                                                                                                       
                                                                                                                                                                                                    
  Current week (all models)                                                                                                                                                                         
  █                                                  2% used                                                                                                                                        
  Resets Jan 31, 12pm (Europe/Warsaw)                                                                                                                                                               
                                                                                                                                                                                                    
  Current week (Sonnet only)                                                                                                                                                                        
  █▌                                                 3% used                                                                                                                                        
  Resets Jan 31, 12pm (Europe/Warsaw)

(built-in '/usage' command).

Answers for the old questions:
Q1: CAB Role - Route Only or Route + Merge?
Route only, lets split its

Q2: Definition of Done (Convoy-Based)
Can we build the acceptance criteria into tasks? Would it help us solve the problem?

Q5: Tests Mandatory at Convoy Level?
Let's say I want >80% test coverage. The more important feature, the more likely I'd like to have a test for it. Let's check how the system behaves and fine tune it later.

Q6: Test Quality Validation via Formulas?
I am not sure I follow. Could you elaborate?

Q8: Token Limit Strategy
This is not a problem in how many agents will work in parallel, but how many token they're gonna burn. A small task can use 15k-30k tokens, detailed scanning of code base for pattern matching alone can burn 50k-60k (and it's only a supporting tool). So I would agree to start with as many agents as is required to run the whole infrastructure plus 3 agents that will add speed. Could you tell me how many agents that would be?

Q10: Validation Thresholds
Coverage >80%, the rest of metrics should be set as a reasonable starting level and tweaked later work in parallel, but how many token they're gonna burn. A small task can use 15k-30k tokens, detailed scanning of code base for pattern matching alone can burn 50k-60k (and it's only a supporting tool). So I would agree to start with as many agents as is required to run the whole infrastructure plus 3 agents that will add speed. Could you tell me how many agents that would be?

Q10: Validation Thresholds
* Coverage >80%
* Mutation score - I don't know this term, please explain
* Cyclomatic complexity: please take best practices from The Internet
* Security: foundational, very strict rules. Best practices are described by many sources.

Answers for new questions:
Q11: Convoy Allocation Strategy
* Do you have many managers of one type? Please elaborate.
* Agents pull from queue is a reasonable approach.
* Priority: if in the dependency tree you have two tickets available on the same level, then priority decides. Any objection?

Q12: Merge Strategy
If a task if developed, tests pass and acceptance criteria are met, I don't care what agent merges with the following exceptions:
* the flow doesn't revert its current
* there's a balance between load on agents - I don't want to wait for the pool of agents to give me a new one if existing can merge. I am not sure I follow how in detail the pool of agent s is designed: all roles can run as many parallel agents if the pool allows, or every role has different upper limit of concurrent agents?

Q13: Failure Recovery via Hooks
* incomplete work in git hooks - please elaborate, that's interesting
* agent restart: agent needs whole previous context. Can git hook store it? The idea of incomplete work - in my view - is associated only with a power loss. So no context saved.
* GUPP - in the article describing Gas Town is information that sessions are cattles (disposable) and all work lives in Beads. Where is here place for git hooks? Please let me understand.
