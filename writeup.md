The starting agent has no data discovery tools and no information about the available databases and context, so it hallucinates schema names, resulting in frequent SQL errors. The iterations included in the submitted exercise were as follows:

| Experiment | Easy | Hard |
|------------|------|------|
| Added tools to explore the schema and read the guides, so the agent can discover available schemas, tables, and guides. | 77.6% | 45.8% |
| Added a `run_query` tool so the agent can execute its query, review the results, and fix mistakes. | 78.6% | 47.4% |
| Updated the prompt to instruct the agent to index on business rules from the guide first, rather than inferring them from column names. | 76.0% | 54.7% |
| Updated the `read_guide` tool to leverage a lookup table between schema and guide filename, since each schema maps to a single guide. This did not impact performance but did use 22% fewer tokens. | 75.5% | 55.7% |
| Updated the system prompt to be less procedural and allow the agent to go back to previous steps to revise. This hurt the easy evaluations but allows longer reasoning on hard questions. | 71.9% | 54.7% |

Note: the evaluation results here are averaged across three runs, since the agent sometimes gives different answers for the same question. Because the evaluation dataset is small, there can be significant variation in scores even for the same configuration.

# Things that did not help

There were many other, more complex experiments that did not consistently improve performance or made things worse. Some of these were quite surprising:

- Added instructions in the system prompt to profile data and check for outliers, including a `profile_data` tool.
- Using a larger, more capable model such as GPT-5.4 at different reasoning levels.
- Changing the temperature.
- System prompt updates, such as switching from procedural steps to phases that allow the model to be more free-form in how it structures its thinking, or dramatically simplifying the prompt. Adding more instructions often made the performance worse. It also frequently changed the behavior of the agent to forget to submit its answer via the tool and instead returns the query json as plain text. 
- Adding a subagent to review the query for correctness, execution reliability, and context alignment. The subagent optionally uses a different LLM model. We tried Sonnet, Haiku, Gemini 2.5 Flash, and GPT-4.1 Mini. None appeared to make a consistent improvement but increased latency and/or cost.
- Adding a subagent to draft the query, taking in database information, the guide, and sample data as context. The subagent optionally uses a different LLM model, e.g., Gemini 2.5 Pro (explicitly fine-tuned for SQL). It did not appear to make a consistent improvement.

# Process

My process for analyzing failures and forming new hypotheses included the following:

- Looking through example failures in the evaluation runs by dumping the results to a CSV, comparing the response query vs. the gold query, and thinking through how I (or a human analyst) would have composed the query based on the available context for that schema, thus forming a hypothesis for why the model landed on the query it did.
- Reading through the reasoning traces for example failures, forming hypotheses for where the model's reasoning may be inadequate.
- Using Claude Code to diagnose failures and summarize patterns across evaluation examples.

# Discussion

A larger model with more reasoning did not seem to help, which immediately seemed suspicious. On reading some of the mismatch evaluation examples, the questions the agent got wrong are quite ambiguous and frequently result from misunderstanding a user's intent or from lack of context (as opposed to failing to retrieve the right context or interpret it). Some examples:

- For the question "What is the on-time performance percentage for each unique airline carrier?" (which relies on finding flights within 15 minutes of scheduled arrival), the gold query uses `ArrDelayMinutes <= 15`, but the agent sometimes uses the binary indicator column `ArrDel15 = 0`. There is no documentation or context indicating which one is correct.
- For the question "Identify the top 30 members (first, last) by cumulative lifetime charges," the agent sometimes returns only the names but not the lifetime charges column. The question does not explicitly ask for this column, even though the gold query returns it.
- For the question "Find the top 30 accounts by total absolute transaction volume, excluding legacy transactions," the guide says "All transactions with k_symbol = 'UROK' (interest) or NULL should be excluded from revenue calculations," but it is unclear whether this rule applies to this question. Nor does the guide state anywhere that `k_symbol = 'UROK'` refers to "legacy transactions," which is what the gold query assumes.

In a real business setting, the quality of the answer from a data agent depends highly on the quality of the context it has access to and the explicitness of the user query. A user may be a deep expert in the business domain, but if that domain knowledge is not spelled out anywhere, no amount of capable reasoning by the agent can answer the question correctly. Similarly, if the user is ambiguous about what they want from the query, the agent cannot read their mind. A human analyst with access to the same information and the same query could easily make the same mistakes.

Note: we used a lookup table to map each schema to a relevant guide, and the entire guide is loaded into the context. All the business rules for each schema reside in a single guide, and building the mapping is relatively straightforward (many guides explicitly state which schema they apply to; if not, it can be inferred from the filename and domain). There is an assumption here that each schema has all its business rules in a single guide, even for unseen data. Since each guide is relatively small (on average ~500 tokens), building a vector store or semantic search to retrieve business rules would be overkill. 

In a real business setting, unless the business rules reside in a massive amount of unstructured, unorganized data, a lookup table can also be maintained as we build out our table schemas. Otherwise, a `grep`-like tool is much simpler than building out a vector store / RAG and can probably get us most of the way there. 

# AI contribution

I used Claude Code for planning and structuring the code. I used Claude Code to create the mapping between schema and guide to save time. This could also be done by hand by looking at the mention of the schema name in the guide, or matching by domain and verifying the data makes sense given the context of the guide. We left out the ambiguous ones. I used Claude Code to output the eval results into CSV format, which allowed me to filter and inspect the mismatch examples easily. I also asked Claude Code to find patterns in the wrong eval results, though the patterns and suggestions it had were sometimes suspect. From these multiple sources, I came up with a mental model for why the evaluation results mismatched and formulated hypotheses for what to pursue next.
