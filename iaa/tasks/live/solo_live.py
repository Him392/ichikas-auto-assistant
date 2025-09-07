from kotonebot import task

from .live import solo_live as do_solo_live
from iaa.tasks.start_game import go_home

@task('单人演出')
def solo_live():
    go_home()
    do_solo_live('single-loop')