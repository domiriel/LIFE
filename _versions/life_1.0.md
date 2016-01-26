LIFE File Format
================
Life 1.0 - 8 Jan 2016   
Copyright © 2016, Daniel Gonçalves - [http://danielgoncalves.info](http://danielgoncalves.info)

---

Introduction
------------
This document describes the syntax of the LIFE file format. This format is meant to record personal lifelogging information about a person's locations through time. It is intended to be both machine- and human-readable, easy to understand and easy to update.


Concepts
--------

Lifelogging is the practice of recording information about oneself. There are many things that lifelogging practitioners record (food, health, mood, sleep, etc.). One of those are locations and activities performed throughout the day. The LIFE format gives us a standard way to record this information which is simple yet expressive, stemming from years of lifelogging practice.

The format is centered around *days*, a given calendar day. For each day, a number of *spans* describe where the user during a particular time interval. Intervals for which no span is specified are considered to be *travelling time*. Another way to look at it is that a span represents a time where you were "indoors", for some time at some place doing something meaningful, and their complement is when you were walking or driving somewhere. 

Spans mention *places*. A place is somewhere that you were at and it is usually described in a personally relevant way. A place is assumed to be tied to a specific physical location. Hence, if there are two 'Tesco' supermarkets in two different streets, the place names should be difference (e.g.: 'Tesco-Foo St.' and 'Tesco-Bar St.').

An exception are what we call *indoors trip*. If you board a subway train or a plane, you will technically be "in the same place" (from your personally relevant point of view), but that "place" is moving. This will result in an atypical span that does not represent a say in a static place but rather in a *"moving place"*.

Each span can be annotated with tags and a personally relevant comment string that can be used, for instance, for short descriptions of what was the purpose of that span (a movie that was seen, person that was met, etc.)

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

#### Tags and Semantics

Optionally, a set of tags can be specified by enclosing them im square brackets ("`[]`"). Different tags should be separated with a pipe character ("`|`").  Also optionally, a *semantic description* can be added inside curly braces ("`{}`"). An example:

    2124-2349: neighborhood cinema [movies|leisure] {Star Wars: The Force Awakens}


#### Indoors Trips

Finally, an indoors trip is represented by including the departure and arrival place, separated by `->`. In the case of indoors trips, the span is assumed to represent actual travel time, not time spent at either place. If you need to specify time spent there, you should explicitly include a span for it:



    1026-1032: saldanha station
    1032-1045: saldanha station->rossio station
    1045-1047: rossio station



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

If done properly, from a LIFE file a user should be able to tell where s/he was at any given moment in time and (if annotated with semantics) what was the purpose of the visit. Categories and tags can also help with this: a place categorized as a restaurant will probably be visited for a meal. It is up to each user to decide what different tags, categories, etc. represent. One person coud use tags to annotate the names of people met at a given place. Another could use it to note where dinner or lunch were had, etc.

One important thing is to maintain things consistent. The same place name should be used recurrently to represent the same place, for instance. Failure to do this may make it hard to compare across spans. This is easier than it appears since for most people there will be a somewhat small set of recurrently visited places (home, work, etc.) and a few that are seldom visited. The recurrent ones will quickly be mechanized. And, of course, tools can be developed to help maintain a LIFE file.
