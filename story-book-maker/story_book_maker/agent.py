from google.adk.agents import SequentialAgent

from story_book_maker.book_assembler.agent import book_assembler_agent
from story_book_maker.illustator.agent import parallel_illustrator_agent
from story_book_maker.story_writer.agent import story_writer_agent

story_book_agent = SequentialAgent(
    name="StoryBookMaker",
    sub_agents=[story_writer_agent, parallel_illustrator_agent, book_assembler_agent],
)

root_agent = story_book_agent
