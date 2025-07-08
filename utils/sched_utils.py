from data.database import Database
from data.config import *
from .channels_u import get_invite_link_stats
from .time_u import get_current_time_formatted

db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)


async def CHECK_LINKS():
    links = db.get_all_active_links()
    for i in links:
        requests = await get_invite_link_stats(i['channel_id'], i['link'], True)
        joins = await get_invite_link_stats(i['channel_id'], i['link'], False)
        print(i)
        link_stats: list = eval(i['stats'])
        last_requests = link_stats[-1][1]
        if requests < last_requests:
            requests = last_requests
        link_stats.append([get_current_time_formatted(), requests, joins])
        db.update_link_stats(i['id'], link_stats)