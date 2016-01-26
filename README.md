LIFE File Format
================
Life 1.1 - 26 Jan 2016   
Copyright © 2016, Daniel Gonçalves - [http://danielgoncalves.info](http://danielgoncalves.info)

---

Introduction
------------
This document describes the syntax of the LIFE file format. This format is meant to record personal lifelogging information about a person's locations through time. It is intended to be both machine- and human-readable, easy to understand and easy to update.


Concepts
--------

Lifelogging is the practice of recording information about oneself. There are many things that lifelogging practitioners record (food, health, mood, sleep, etc.). One of those are locations and activities performed throughout the day. The LIFE format gives us a standard way to record this information which is simple yet expressive, stemming from years of lifelogging practice.

The format is centered around *days*, a given calendar day. For each day, a number of *spans* describe where the user during a particular time interval. Intervals for which no span is specified are considered to be *travelling time*. Another way to look at it is that a span usually represents a time where you were "indoors", for some time at some place doing something meaningful, and their complement is when you were walking or driving somewhere. 

Spans mention *places*. A place is somewhere that you were at and it is usually described in a personally relevant way. A place is assumed to be tied to a specific physical location. Hence, if there are two 'Tesco' supermarkets in two different streets, the place names should be difference (e.g.: 'Tesco-Foo St.' and 'Tesco-Bar St.').

An exception are what we call *trips*. A trip is a special kind of span where instead of just one place, two are mentioned. These are the origin and destination of a trip the user has made. They can be used to annotate useful information about that trip (see below).

Each span can be annotated with tags and a personally relevant comment string that can be used, for instance, for short descriptions of what was the purpose of that span (a movie that was seen, person that was met, etc.). Also, additional tags for specific periods of time inside a span can be specified.

Finally, LIFE gives support for several meta information regarding the categories of places, their physical location, place inclusion (a restaurant inside a shopping mall, for instance), etc.


Syntax
------

### Day 

One day is represented by a header indicating the date. The format for the date is `"yyyy_mm_dd"`, and it must be preceeded by two hyphens (`"--"`). After the header, there should be a line per span, as described below. All spans should be contiguous (no blank lines in between). There should be spans covering the entire day.

---
### Span

A span, in its simplest form, is represented as follows:

    <start>-<end>: <place>

`<start>` and `<end>` are the starting and finishing time of the span. Precision is down to the minute. They follow military time standard, `hhmm`: 3:32PM becomes `1532`. 8:21am is `0832` and so on. Times begin at `0000` and end at `2359`. 

 `<place>` can be any string, for a personally relevant place name ("home", "brother's home", "sam's school", etc.). A complete span could be:

    1241-1343: mcdonalds close to work

A span must start at the beginning of a line (no whitespace).

#### Tags and Semantics

Optionally, a set of tags can be specified by enclosing them im square brackets ("`[]`"). Different tags should be separated with a pipe character ("`|`").  Also optionally, a *semantic description* can be added inside curly braces ("`{}`"). An example:

    2124-2349: neighborhood cinema [movies|leisure] {Star Wars: The Force Awakens}


#### Trips

A trip is a special kind of span represented by including the departure and arrival place, separated by `->`. The span is assumed to represent actual travel time, not time spent at either place. If you need to specify time spent there, you should explicitly include a span for it:



    1026-1032: saldanha station
    1032-1045: saldanha station->rossio station
    1045-1047: rossio station


#### Sub-Span Annotations

Sometimes, it may be relevant to provide additional information about some of the things done in a particular span. For instance, a trip may have consisted of different stretches, using different modes of transportation. So, while the user may want to specify only one Trip, it may be interesting to specify the time intervals, inside it, where those different modes of transportation were used. To do that, we use *sub-span annotations*.

A sub-span annotation is written by indenting the line using at least one space character (`' '`). After, the user can specify either a time interval (`1254-1301`), in the same format as for a span, or a single time instant (`1643`). This will tell either the **interval** or the **instant** that is being annotated. Then, after a semicolon, a set of tags in the same format as for spans can be specified. For instance, for interval annotations:

    1254-1335: work->home ; a trip from work to home that we'll annotate below
       1254-1303: [walk]
       1303-1311: [stop]
       1311-1328: [bus]
       1328-1335: [walk]
       ; annotations for mode of transportation

or, for instant annotations:

    1823-2102: le bistro [dinner]
       1943: [ice cream]    ; an ice cream was eaten at that time


Interval Sub-Span annotations could be replaced by actual spans or trips for that interval, of course. They should be used when the actual place names do not matter. There is no obligation for the annotations to cover the entire time interval of a span or trip. For instance, if the user only wants to record bus travels:


    1254-1335: work->home ; a trip from work to home that we'll annotate below
       1311-1328: [bus]
       ; annotations for bus travels only


---
### Timezone

Sometimes, when moving, we change timezones. We can specify this by indicating the timezone directly in the file. Timezones are represented as offsets from UTC and take the for of `UTC(+/-)<offset>`. For instance, `UTC+2`, `UTC-5`, etc. are all valid. You can also use `UTC` alone, for that timezone. Timezone commands should appear inside a day and are in effect from that moment on, for all spans of that day and subsequent ones, until another timezone command is found. So, usually, in the first day of a file, you'd start with a line for the timezone where you usually are in.

Sometimes, a timezone changes as the result of an indoors trip. For instance, you can board a plane in one timezone and leave it in another. In that case, the correct choice is to see that the departure place of the indoors trip is in one timezone and the finishing place in another. We can specify this by starting an `UTC` command with an `@` sign. So, in the following case, `LIS Airport` would be in `UTC` and `CDG Airport` in `UTC+1`. All spans after the indoors trip are also in `UTC+1`.


    --2011_05_23
    UTC
    0000-0512: home
    0543-0735: LIS Airport
    @UTC+1
    0735-1049: LIS Airport->CDG Airport
    1153-2359: Hotel Foo


Please note that daylight savings time will change your timezone. So, the day they start (or cease) being into effect you should explicitly note this change in the file:

    --2011_03_29
    UTC+1
    0000-0812: home
    0843-1235: work
    1243-1330: restaurant [lunch]
    1338-1749: work
    1823-2359: home [dinner]


----
### Meta Commands

There are several commands that, while not describing a span, convey information that helps understand them. They must be entered *outside* of a day. They all start with an at sign (`@`). Spaces are allowed as padding around the place names and other parameters. Unless otherwise noted, `@` commands should be global: regardless of where they appear in the file, they apply to all days/spans in it.



#### Place Inclusion

Some places are within other, e.g. a particular store inside a shopping mall. How to record it? If you record the store as its own place, you wouldn't know you were in the mall at that time. If you record the mall, information about where you actually went in there would be lost. To circumvent this problem, we can specify place inclusion by connecting a sub and super-place with a `<` sign:

    @a store in the mall<the mall


#### Canonical Locations


It may be relevant, for some applications, to know exactly where (geographically) a place is located. You can use `@` to connect a place with its location, in decimal `lat,lon` format:

    @work @ 32.4343534,-9.54353


#### Place Categories

We can specify categories for places. This will allow you to see your life in broader categories (when you spent time shopping, or going to movies, etc.). This is done by entering the place name, a semicolon and the category name:

    @Radio Shack:Commerce

Category commands are time-sensitive:the category applies for spans after it has appeared. A second category command for a same place replaces that category for that place for that moment onwards. This allows for categorical changes. For instance, a place could be a 'Restaurant' until you go work there, and then it becomes 'Work'.



#### Name Changes

Over large periods of time, places can change names. A restaurant can close and another one open in the same place with another name. Name changes can be specified with a `>>` connecting the old and new place names. Unlike other `@` commands, this one is time-sensitive: the name change is supposed to occur at the time the `@` command appears.

    @ye olde restaurant>>super-duper new bisto



---
### Comments

Comments can be entered into the file by preceeding them with a semicolon (`;`). Everything after it will be considered to be a comment.



## Usage

The point of a LIFE file is to record a person's live from their point of view. Things that are personally relevant, in the way they are so. It should usually begin with a first day, the first line of which will be the default timezone (don't forget to take into account the daylight savings, if relevant). Then we will find a succession of days. Each day should have a span for whenever the user was in some place. The names of the places, as stated above, aren't necessarily the "official" names, but rather what that place means for the user. Place Inclusion can be used to tie those names to the "official" ones if needed.

If done properly, from a LIFE file a user should be able to tell where s/he was at any given moment in time and (if annotated with semantics) what was the purpose of the visit. Categories and tags can also help with this: a place categorized as a restaurant will probably be visited for a meal. It is up to each user to decide what different tags, categories, etc. represent. One person could use tags to annotate the names of people met at a given place. Another could use it to note where dinner or lunch were had, etc.

One important thing is to maintain things consistent. The same place name should be used recurrently to represent the same place, for instance. Failure to do this may make it hard to compare across spans. This is easier than it appears since for most people there will be a somewhat small set of recurrently visited places (home, work, etc.) and a few that are seldom visited. The recurrent ones will quickly be mechanized. And, of course, tools can be developed to help maintain a LIFE file.


## Examples

Below is a sample LIFE file. It shows several use cases for the format and, as such, is heterogeneous in representation level. Usually you would want to avoid this and choose an uniform amount of detail and conventions for your LIFE files.

    ; LIFE for John Doe

    ; First couple of days: the simples use case. Just record when you were somewhere
    --2016_01_01
    UTC                           ;setting the "default timezone"
    0000-1231: home
    1245-1356: McDonalds          ;quite sad, lunching on a mcdonalds on New Year's Day...
    1413-2359: home

    --2016_01_02
    0000-1002: home
    1139-1602: home               ;went for a walk and came back home
    1703-1830: shopping mall
    1830-2045: beef delight
    2201-2359: home

    @beef delight<shopping mall   ; the restaurant is inside the mall!



    ; now, we'll see some tagging and annotation. For instance, John decides to tag where he eats, 
    ; and which movies he watches

    --2016_01_03
    0000-0721: home
    0801-1202: work
    1223-1303: Pizza Place [lunch]                  ; tagged as a lunch place
    1321-1802: work
    1827-2101: Stellar Cinemas [movies] {Deadpool}  ; tagged as movie theater, semantics tells which movie  
    2107-2143: burger king [dinner]                 ; tagged as a dinner place
    2227-2359: home

    --2016_01_04
    0000-0725: home
    0807-1215: work
    1231-1330: Le Bistro [lunch]
    1342-1812: work
    1837-1845: supermarket
    1855-2359: home   [dinner]


    ; next day, John will travel by plane to meet a client

    --2016_01_05
    0000-0810: home
    0000-0912: LIS                 ; Lisbon airport
    @UTC+2                         ; in the next span, the first time will be UTC, the second UTC+2!
    1055-1655: LIS->ATH  [lunch]   ; The trip was actually only 4 hours, but we changed timezones. Had lunch on board!
    1655-1732: ATH
    1901-2359: hotel [dinner]

   
    ; next day, we're still in UTC+2
    --2016_01_06
    0000-0801: hotel
    0831-1243: client
    1301-1358: QuickFoods [lunch]
    1403:1754: client
    2003-2359: hotel [dinner]


    ; heading back home! New timezone change!
    --2016_01_07
    0000-1143: hotel
    1232-1403: ATH [lunch]   ; had lunch at the airport
    @UTC
    1404-1632: ATH->LIS      ; 4 hour trip again, but appears to be two due to timezone change
    1632-1743: LIS
    1831-2359: home



    ; John now decides to annotate his mode of transportation. First, using tags on trips. Not relevant when he
    ; changed transport, only that he used different mods
    --2016_01_08
    0000-0715: home
    0715-0801: home->work [walk|bus]
    0801-1216: work
    1216-1229: work->Le Bistro [walk]
    1229-1342: Le Bistro [lunch]
    1342-1358: Le Bistro->work [walk]
    1358-1812: work
    1812-1837: work->home [walk|bus]
    1837-2359: home   [dinner]



    ; Now using a different trip line for each leg of the trip, to know where and when he changed mode of transportation
    --2016_01_09
    0000-0705: home
    0705-0712: home->bus stop close to home [walk]
    0712-0734: bus stop close to home 
    0734-0801: bus stop close to home -> bus stop close to work [bus|bus:767]  ; rode bus 767
    0801-0811: bus stop close to work -> work [walk]
    0811-1211: work
    1211-1219: work->Le Bistro [walk]
    1219-1331: Le Bistro [lunch]
    1331-1350: Le Bistro->work [walk]
    1350-1822: work
    1822-1824: work->bus stop close to work [walk]
    1824-1825: bus stop close to work
    1825-1841: bus stop close to work->bus stop close to home [bus|bus:767]
    1841-1848: bus stop close to home->home [walk]
    1848-2359: home   [dinner]

    ; 'bus:767' is a normal tag. John decided that he would annotate all bus lines using the 'bus:<number>' convention



    ; John decided he doesn't need to know the places where he gets on buses, etc. after all.
    ; so he'll use simply the sub-span annotations

    --2016_01_10
    0000-0705: home
    0705-0811: home->work
       0705-0712: [walk]
       0734-0801: [bus|bus:767]
       0801-0811: [walk]
    0811-1211: work
    1211-1219: work->Le Bistro [walk]
    1219-1331: Le Bistro [lunch]
    1331-1350: Le Bistro->work [walk]
    1350-1822: work
    1822-1848: work->home
       1822-1824: [walk]
       1825-1841: [bus|bus:767]
       1841-1848: [walk]
    1848-2359: home   [dinner]
       2201: [water:33cl]          ; drank 33cl of water at 2201


---
## Changelog

#### v1.1 - 26 Jan 2016

* Extended support for recording trips between places
* "Indoors trips" are now just trips
* Introduced "Span Annotations", both interval and instant
* Added "Examples" section
