---
name: lookup
track: core
kind: live_api
provider: Tavily
requires_env: [TAVILY_API_KEY]
inputs: [query, topic, timeframe, max_results]
outputs: [items]
side_effect: false
---
# lookup

Searches the web via Tavily. Has a `topic` (`general` or `news`, default `general`) and a `timeframe` argument. You can also specify `max_results` to limit the number of results returned. If you search for news, do not include `news` in the query, use `topic=news` instead. Timeframe can be `day`, `week`, `month`, or `year`. 
