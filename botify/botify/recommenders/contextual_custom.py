from collections import defaultdict
from .random import Random
from .recommender import Recommender
from .indexed import Indexed
import random


class ContextualCustom(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, recommendations_redis, catalog):
        self.tracks_redis = tracks_redis
        self.fallback = Indexed(tracks_redis, recommendations_redis, catalog)
        self.catalog = catalog
        self.long_listen = defaultdict(set)

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        if prev_track_time > 0.7:
            self.long_listen[user].add(prev_track)
        else:
            self.long_listen[user].discard(prev_track)

        if not self.long_listen[user]:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        prev_track = random.choice(list(self.long_listen[user]))
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if recommendations is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        return random.choice(recommendations)
