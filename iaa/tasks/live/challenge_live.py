from kotonebot import task

from .live import challenge_live as do_challenge_live
from iaa.config.schemas import GameCharacter
from iaa.tasks.start_game import go_home

@task('挑战演出')
def challenge_live():
    go_home()
    do_challenge_live(GameCharacter.Ichika)