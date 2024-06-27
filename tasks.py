from robocorp.tasks import task
from robocorp import workitems
from lib.scrapers.rpa_reuters import Scraping

@task
def minimal_task():
    payload = workitems.inputs.current.payload
    print("Received payload:", payload)
    result = Scraping(
        phrase = payload.get('phrase'),
        section = payload.get('section', 'Breakingviews'),
        months_ago = payload.get('months_ago')
    ).start_scraping()
    print(F"Status task: {result}")
