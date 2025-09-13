# Task

I'd like to have a command line interface for flow. It should look like this:


flow [command]

Commands are
- start, stop, ask, summarize, preferences, find, monitor, serve


For now please implement start and stop which starts and stops screen recording. By default it should reocrd all screens but it takes a flag called main-screen-only that can be set to true that then records only the main screen.

I want the ask command to consider what tools are available and then make a selection. Tools are find and summarize

find should be when the user is trying to look up something specific. Ask summarize should be used when the user asks for a summary. Otherwise it should share a message about no tool match and explain what it's able to do. The summary tool should figure out the day range and summarize by hour, day, or month. This summary should be done using Map Reduce I think meaning break the problem into smaller chunks and then combine. This is for the chromadb search so that we get a summary of summaries. Also please figure out a good way to sampel from chromadb for this -- I'm not sure if this is supported or not. And maybe the best way is to keep a running hourly-summaries folder and daily-summaries folder that's used for this so that we can actually generate summaries of all the data via a rollup process in the case of need daily-summary data by doing hourly summaries and then sumamrizing the hourly sumamries into daily summaries. The same thing should be done for monthly or yearly. For ranges that have already been summarized by default don't resumamrize and again use the three prompt approach to figure out what the user wants to.


We'll need to run a small model on device so please do that to handle tool calling. I want it to be self contained so maybe use docker? But setup should show progress bars for installation

the monitor command should show memory usage, cpu usage, processing time in real time for what's happening. Along with total number of screenshots saved and days covered. Ex: 12k screenshots and installed 21 days ago.

the preferences command should be a simple file that has preferences at this point just whether all screenshots are saved or just for the main monitor by default. Defaults to all screens


flow serve should start the MCP service that's used by other GUIs (Claude Desktop, etc.)

By default flow serve should be started with flow start and stopped with flow stop.

I'm not sure how to do documentation and I want to make sure folks that love to read documentation in the terminal love this project. So Please make sure it's documented in a way that makes the man pages good. Also I want to post the documentation online so please do that as well. Find a good example or two and use that as inspiration.

There are also security and privacy concenrs and that's why this project is open source. So other oflks can take a look at the code and make sure it's safe. But please thikn about that.

Lastly there are size and space concerns. These metrics should be shown in the flow monitor. As Disk Space Usage for ChromaDB and for Screen History.

Also please generate a file with a list of other tools that would be useful when searching. I'd like to have a list of additional tools that I may add in the future and if it's possible to make a tool that detects when a user is doing something that doesn't fit into our current tools but could be handled by a new tool. I want a prompt to show up that says in looks like you're doing XYZ, and we don't have a tool for that yet. But click this link to open a PR in github that Joe will look at. Then say you can disable these prompts by clicking XYZ button and if they do update the preferences. This should only be shown once. Or there should be three options. Yes, No, Don't show again.

The last thing I want you to figure out is how to make it easy to share a link so that other people can search via a MCP client. I think this means I'll need to hoast a public MCP server and for now I want to set that up using ngrok.

And there's a lot of existing code already. Please use it only if it's useful and good. Otherwise feel free to change it.


1. Please make a plan file called PLAN.md
2. Then ask me for feedback on the plan or to approve. If I give feedback then you should update the plan. Otherwise please generate a checklist in Checklists.md of items to work through
3. Please work through the checklist in order.

Notes:
Please make sure to commit all your changes to the repo after each step.

