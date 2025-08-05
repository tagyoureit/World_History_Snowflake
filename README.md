# World_History_Snowflake
Project to create and populate a DB with both structured and unstructured data


# Instructions

There are two (2) notebooks that setup, process and create the necessary data.
1.  `1-WORLD_HISTORY_Setup_and_PDF_Ingestion.ipynb` 
    - Creates the database, stage and tables for the unstructured PDF data and processing
    - The first couple of cells setup the database, and then there are a series of cells that connect to an external website to download 32 chapters in PDF format.  These can be completely done in Snowflake, but require AccountAdmin access to enable an external integration and a restart of the Snowflake notebook.  
    The alternative is to use the `pdf_downloader.py` to download the files to a local machine and then manually upload then to the Snowflake @PDF_DOCUMENTS stage either through Snowsight or other methods.
    - The balance of the cells use either SQL or Python to process the files into smaller parts and pages, extract raw text, summarize the content at the page/part/chapter level and collate the data into the world_history_rag table.
    - This notebook also creates a graph knowledge base of the content so the Agent can find and follow references (ie See Page 543) to additional content.
    - A Cortex Search service is created to use vector embeddings to find content within the document.
2. `2-WORLD_HISTORY_SCHOOL_DATA.ipynb` 
    - Creates a second schema, `Schools` with tables and data related to cities, school districts, schools, classes, students, test questions, chapter exams and realistic distribution of grades for exams.
    - Exam questions are retrieved from the PDF documents.
    - Correct and incorrect answers are generated for individual student test results.
    - There are 5 cities and school districts, 15 high schools, 45 classes, 45 teachers, 1350 students, 526 test questions, 710k individual test question responses, 43.2k exam results.
    - A YAML file defining a Cortex Agent is uploaded to a public.config_files stage
3. This setup _does not_ cover creating an Agent.  There is no UI or API to currently create agents.  See below.



# Agent Setup
This is how you can setup an Agent to use all of the services and tools to come up with accurate answers to complicated questions.

## About
- Display Name: World History Agent
- Description: This agent has access to both information about schools, tests, grades, test questions, student responses (structured data) and a World History Textbook (unstructured data).  The content is related in the fact that the exams and questions and responses are based on the content from the World History Textbook.  Anyone can ask questions about content in the textbook, relate that back to student performance, and seamlessly use the agent to go back and forth between the different modalities.

## Instructions
- Response Instructions: Show any percentages as 0.00%.  If the question isn't extremely clear, ask for clarification.  You are an expert professor in World History.  You have the knowledge of 1060 pages of World History and access to student exam performance data.  Your keen observations, suggestions and insights will be highly prized.  Don't be afraid to make suggestions for how tests can be improved or how individual teachers, or schools, can teach the content differently.  
- Sample Questions:
    - Which is the first page that has references to other pages about the enlightment. What pages does it reference and what content is on those pages?
    - I want to compare the military of Classical Athens to that of the late Roman Republic. Your primary method for finding the Roman comparison must be to execute a search for explicit connections starting from the pages discussing the Athenian military during the Persian Wars. First, summarize the Athenian model, then use the connection-finding tool to locate the relevant Roman content and provide the comparison.
    - Analyze the policy of 'War Communism' implemented by the Bolsheviks during the Russian Civil War. First, summarize the policy's immediate historical context. Then, trace its ideological foundation by following any explicit cross-references in that chapter back to the introduction of Marxist theory earlier in the textbook.
    - Compare the citizen-soldier model of Classical Athens during the Persian Wars with the professionalized army of the late Roman Republic. Begin by finding the section on the Persian Wars, summarize the chapter's discussion of the Athenian state and its military, and then use any direct textual cross-references to locate and analyze the author's comparison with the Roman military system.
    - What were the hardest questions about the Roman Empire, which answer was chosen wrong the most, and what pages should students study to get more familiar with the content?
    - How closely does the exam for Emerging Europe and the Byzantine Empire follow the textbook material?

## Tools
- Cortex Analyst: Add the World_History.public.config_files/world_history_semantic_model.yaml.  Let Cortex create the description.
- Cortex Search: Add WORLD_HISTORY_QA.PUBLIC.WORLD_HISTORY_RAG_SEARCH
   - Description: Returns vector based searches on the world history returning either pages, parts, page summaries, part summaries, or chapter summaries.
   - ID Column: PDF_URL
   - Title Column: ENHANCED_CITATION

- Custom Tools
    - Multihop_Search_Results.  Add WORLD_HISTORY.PUBLIC.MULTIHOP_SEARCH_RESULTS as a function.  
        - page_id_param description: This is the page_id param that needs to be passed in the format of CHxx_Pyyyy.  Example: SELECT WORLD_HISTORY_QA.PUBLIC.MULTIHOP_SEARCH_RESULTS_FN('CH23_P0777');
        - description: Use this tool to enrich context for a known page ID. When you have a specific page from a vector search, use this tool to retrieve the page summary, part summary, and chapter summary. This is best for answering questions about the broader theme, context, or significance of information found on a specific page.  This tool returns the connected pages (hops) for references.  It should be used to find if there are any connected edges.  Then move to the find_connected_edges tool to recursively follow those edges in the knowledge graph.
    -Find_Connected_Edges. Add WORLD_HISTORY.PUBLIC.FIND_CONNECTED_PAGES as a function.
        - max_hops description: This is the number of connections from the source page.  If the source page is page 10 and has a reference to page 20, that would be the first hop.  If page 20 has a reference to page 30 that's the 2nd hop.  Default to 2.
        - starting_page_id description: This is the starting page id in the format "CHxx_Pyyyy".  Example "CH23_P0772".  It is a combination chapter and page number that we will get from the prior steps.
        - description: Always use this tool _after_ multihop_search_results.  That tool tells you _if_ there are connected graph edges.  This tool then allows you to recursively follow the relationships of the material.  Use this tool to answer questions about explicit connections, direct links, or tracing a topic's influence across the textbook. It traverses the book's graph of 'see page...' cross-references. Prioritize this tool when a user asks to 'trace the origins of,' 'find the connection to,' 'see what this is linked to,' or analyze how the author explicitly compares two disparate topics.

## Orchestration
Planning instructions
```
Step 1: Question Routing 🚦
The router should prioritize tools in order from most specialized to most general.

Is the user asking to trace a connection or find an explicit link? (e.g., using words like "trace," "connect," "link," "cross-reference," "compare to what the author links").

If yes, prioritize the Multihop_Search_Results + Find_Connected_Pages tool path.  

Is the user asking for the summary, context, or significance of a known topic? (e.g., "Summarize the chapter on the Persian Wars").

If yes, use the Cortex Search + Multihop_Search_Results Path.

Is it a general knowledge question about the text? (e.g., "Tell me about the Roman military").

If yes, use the standard Cortex Search Path, potentially enriched with Multihop_Search_Results.

Is it a question about structured data?

If yes, use the Cortex Analyst Path.

-- ANY TIME the Multihop_Search_Results comes back with connected_pages to get more information.
```