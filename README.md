# QuickQuack [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Overview
The ~~Fast Duck~~ QuickQuack skill rating system is specifically designed for time-based games, such as racing games, where players strive to achieve the fastest completion times on various maps. It addresses key challenges commonly encountered in such games:
* Many time-based games feature a large number of maps, ranging from hundreds to thousands. This can result in situations where a map lacks sufficient "saturation" to provide a balanced rating for players who complete it. Factors contributing to this lack of "saturation" may include a low player base, the map's lack of popularity, or its high level of difficulty, making successful completion a significant challenge.
* Time-based games typically operate as "infinite games," allowing continual access to maps throughout the game's lifespan and enabling ongoing alterations to leaderboards.

# Key Principles
* Seasons should have a relatively short duration, allowing even casual players to actively participate from start to finish (e.g., 2 weeks).
* The map pool should encompass maps that test a variety of skills. Additionally, the pool should not be overly extensive to ensure that even casual players can engage with all the maps within the given time period (e.g., the number of days in a season multiplied by 1.5).
* To receive a rating for the current season, players must successfully complete a specified number of maps from the pool within a designated time frame (e.g., the number of maps in the pool multiplied by 0.5). Only times recorded during the specific period should be considered.
* To maximize map saturation, the rating system should encourage players to play maps that have a low record count.
* For the season's final rating to be compatible with any future seasons, it is crucial to normalize the number of players, maps, and records.

# Calculations
WIP

# Sample Implementation
This repository includes a proof-of-concept sample implementation of the system. It is important to note that this implementation is heavily unoptimized and should not be utilized in a production environment.
While there is some boilerplate code, those interested in understanding the QuickQuack implementation can begin by reviewing the `add_record` method. 
In addition, there are methods to dump and load JSON files, making it easy to inspect numbers in the database.
There is also a `populate_database` method designed to simulate "real-world" data, although it is an big approximation. This simulation involves randomly setting parameters such as:
* Map popularity
* Absolute player skill
* Player skill uncertainty
* Player number of tries for each map

This approach allows for the comparison of "expected results" with the "actual results" produced by QuickQuack. Following several tests, I can confirmed that QuickQuack is indeed working and yields the intended outcomes. 😄

# Additional Ideas:
* The map pool selection can be customized, either handpicked, semi-random, or chosen through community votes. It could also include new maps specifically released for a particular season.
* At the conclusion of each season, players could be awarded "badges" for achieving specific milestones, such as securing 1st, 2nd, and 3rd place on individual maps and on final leaderboard. An additional achievement might be earned for recording a time on every map in the pool. Many other achievements could be explored. The key aspect is visibility of those badges, they should be displayed in a player's profile as attractive graphical icons, serving as strong motivation to participate in the season.
* Historical season results should be easily accessible, everyone loves statistics!

# How to make it work outside defined seasons
In order to implement the system outside defined seasons, a straightforward approach is to assign each player their individual map pool, consisting of the X number of maps where the player performed the best. However, it's important to note that calculating skill ratings across thousands of maps, over an infinite time period, and with numerous inactive players will result in less accuracy compared to restricting the system to specific defined values.

I would recommend avoiding the use of just one long-term rating. Perhaps a good solution would be to have two ratings: the first being short-term and accurate, and the second being long-term and approximate. The long-term rating can be calculated using the above approach or simply be the average of all (or just the latest) short-term ratings.

# License
[MIT](License)
