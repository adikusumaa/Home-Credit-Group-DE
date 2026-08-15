from crewai import Crew, Process
from crewai_agents.agents import analyst, engineer, reviewer
from crewai_agents.tasks import task_analyze, task_fix, task_review

incident_crew = Crew(
    agents=[analyst, engineer, reviewer],
    tasks=[task_analyze, task_fix, task_review],
    process=Process.sequential,
    verbose=True
)