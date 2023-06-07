# -*- coding: utf-8 -*-
import os
import datetime
import time
import copy

###############################################################################
#####################  LIFE format reader/writer v2.1  ########################
###############################################################################
# This is a Python module to read and write LIFE files. LIFE is a simple text # 
# format to represent a life, as a set of days, each with a set of spans.     #
# Spans are time intervals during which the person was somewhere. See         #
# https://github.com/domiriel/LIFE for info on the file format and usage      #
###############################################################################
# This module is released under the MIT license.                              #
# (c) 2016-2023 Daniel Gonçalves                                              #
###############################################################################


############################################################
################  Auxiliary Functions  #####################
############################################################


def military_to_minutes(ts):
    """converts a timestamp in 'military format' (ex: '1243') to the number of
    minutes since the day began
    """
    h = int(ts[:2])
    m = int(ts[-2:])
    return h*60+m



def minutes_to_military(minutes):
    """converts no.of minutes since day began to 'military format'(ex:'1243')"""
    h = minutes / 60
    m = minutes % 60
    tmp = "%2d%2d" % (h, m)
    tmp = tmp.replace(" ","0")
    return tmp



def timezone_offset(timezone):
    """Given a timezone in format UTC(+/-)<offset>, returns the offset
    (0 is returned if the timezone is simply "UTC").

    ex: timezone_offset("UTC+3") -> 3
    """
    timezone = timezone.lower()
    if timezone=="utc":
        return 0
    else:
        return int(timezone[3:])


def timezone_from_offset(offset):
    """Given an offset (integer), returns a timezone in the format
    UTC(+/-)<offset> (or simply 'UTC' if the offset is zero.

    ex: timezone_from_offset(-3) -> "UTC-3"
    """
    if offset==0:
        return "UTC"
    elif offset>0:
        return "UTC+"+str(offset)
    else:
        return "UTC"+str(offset)



############################################################
#################  Auxiliary Internal  #####################
############################################################

def unique(lst):
    """return list with unique elements from argument list"""
    res = []
    for l in lst:
        if not l in res:
            res.append(l)
    return res


def well_formed_date(day,hour):
    """Converts day, time in .life format to ISO format string"""
    d = day.replace("_","-")
    hour = minutes_to_military(hour)
    d = d+"T"+hour[:2]+":"+hour[-2:]+":00"
    return d


def tomorrow(last_date):
    """get next day, in "yyyy_mm_dd" format"""
    tmp=datetime.datetime(int(last_date[:4]),int(last_date[5:7]), int(last_date[8:10]))+datetime.timedelta(days=1)
    return "%4d_%02d_%02d" % (tmp.year,tmp.month,tmp.day)

def yesterday(last_date):
    """get previous day, in "yyyy_mm_dd" format"""
    tmp=datetime.datetime(int(last_date[:4]),int(last_date[5:7]), int(last_date[8:10]))+datetime.timedelta(days=-1)
    return "%4d_%02d_%02d" % (tmp.year,tmp.month,tmp.day)



############################################################
########  Life Class: a set of day records  ################
############################################################

class Life:
    """A set of days, encompasing a life, plus meta-commands"""
    def __init__(self, filename=None, default_timezone="UTC", debug=False):
        self.days=[]             # the list of days
        self.categories={}       # the place categories
        self.subplaces = {}      # the subplaces
        self.superplaces = {}    # the superplaces (reciprocal of subplaces)
        self.nameswaps={}        # names that have changed for the same location
        self.locationswaps={}    # different things at the same place
        self.coordinates={}        # known locations for places (lat, lon)
        self.default_timezone=default_timezone  # the default timezone
        self.basepath=""
        self.debug=debug
        
        if filename:
            self.from_file(filename)

    def __iter__(self):
        for d in self.days:
            yield d


    def __getitem__(self, ndx):
        if type(ndx)==int:
            return self.days[ndx]
        else:
            return self.day_at_date(ndx)


    def day_at_date(self,date):
        """Return day for a particular date."""
        for d in self.days:
            if d.date==date:
                return d
            elif d.date>date:
                return None
        return None

    
    # TODO: Add days programatically (not from file)
    # TODO: Output .life file (to_file method)
        
    def update_day_from_string(self, date, content):
        """Updates day with content from a LIFE string"""
        for i in range(len(self.days)):
            if self.days[i].date == date:
                self.days[i] = self.from_string(content, replace=True)


    def remove_day(self, date):
        """Removes day from LIFE"""
        for i in range(len(self.days)):
            if self.days[i].date == date:
                self.days.pop(i)
                return


    def from_string(self, content, recursive=False):
        """Populates instance from a .life file"""

        if type(content) is str:
            content = content.replace('\r\n', '\n').split('\n')

        if not recursive:
            self.curday=None
            self.curdate=None
            self.curtimezone = self.default_timezone            
        for line in content:
            try:
                line=line.strip().lower()                
                line = line.split(";")[0]
                if len(line)==0:
                    pass
                elif line[:2]=="--":
                    if self.curday:
                        self.days.append(self.curday)                    
                    self.curdate = line[2:].strip()
                    self.curday = Day(self.curdate)    
                elif line[:3] == "utc":
                    self.curtimezone = line
                elif line[:4] == "@utc":                    
                    self.curtimezone = [self.curtimezone,line[1:]]                    
                elif line[0]=="@":
                    self.parseMeta(line[1:],self.curdate)
                elif line[0]==">":                    
                    self.curday.add_note(line[1:].strip())
                else:
                    dates,descr = line[:line.find(":")],line[line.find(":")+1:]
                    descr=descr.lower()
                    self.curday.add_span(Span(self.curdate,dates[:4],dates[-4:],descr.strip(),self.curtimezone))
                    if type(self.curtimezone) == list:
                        self.curtimezone = self.curtimezone[1]
            except ArithmeticError:
                print("Failed: ",line)
        if self.curday:
            self.days.append(self.curday)
        if not recursive:
            del(self.curday)
            del(self.curdate)
            del(self.curtimezone)            



    def from_file(self, filename, recursive=False):
        """Populates instance from a .life file"""
        self.from_string(open(filename,"r",encoding="utf8").read(), recursive=recursive)
       


    # TODO: From MySteps. Unsure if this works as is, most likely not. Needs to preserve comments, etc.
    def to_file(self, path):
        """Creates a file in the LIFE format"""
        f = open(path, "w", encoding="urf8")
        f.write(repr(self))
        f.close()


    def parseMeta(self, line, date):        
        """Parses meta-commands ("@<command>")"""
        if ">>>" in line:  # Something new in the same location ("@oldname>>>newname")
            a,b = line.split(">>>")
            a=a.strip()
            b=b.strip()
            self.locationswaps[a]=(b, date)
        elif ">>" in line:  # A location that changed names ("@oldname>>newname")
            a,b = line.split(">>")
            a=a.strip()
            b=b.strip()
            self.nameswaps[a]=(b, date)
        elif "<" in line: # subplace ("@subplace<superplace")
            a,b = line.split("<")
            a=a.strip()
            b=b.strip()
            self.subplaces[b]=self.subplaces.get(b,[])+[a]
            self.superplaces[a]=b
        elif ":" in line: # category            
            a,b = line.split(":")
            a=a.strip()
            b=b.strip()
            self.categories[b]=self.categories.get(b,[])+[a]
            # TODO Names that change location
        elif "include" in line:            
            #print("reading from file %s" % os.path.join(self.basepath,line.split(" ")[-1].strip()[1:-1]))
            self.from_file(os.path.join(self.basepath,line.split(" ")[-1].strip()[1:-1]),True)
        elif "@" in line: # place location ("@oldname @ 38.736347, -9.140768")
            place,loc = line.split("@")
            place = place.strip()
            a,b = loc.split(",")
            a=float(a.strip())
            b=float(b.strip())
            self.coordinates[place]=[a,b]


    def placename_at(self,place,date):
        """Get name of a place at a specific date, based on existing nameswaps ("@... >> ...")"""
        if place in self.nameswaps:
            if self.nameswaps[place][1]>date:
                return place
            else:
                return self.placename_at(self.nameswaps[place][0], date)
        else:
            return place


    def current_placename(self, place):
        """Get current name of a place, based on existing nameswaps ("@... >> ...")"""
        return self.placename_at(place, self.days[-1].date)
    

    def update_places(self, day):
        day = copy.deepcopy(day)
        changes = {}
        for p in day.all_places():
            changes[p]=self.current_placename(p)
        day.update_placenames(changes)
        return day

        
    def update_to_superplaces(self, day):
        day = copy.deepcopy(day)
        changes = {}
        for p in day.all_places():
            changes[p]=self.superplaces_of(p)        
        day.update_placenames(changes)
        return day


    # From MySteps. TODO: make sure this honors all comments, meta, etc. (apparently only the days)
    def __repr__(self):
        """Converts LIFE object to LIFE format string"""
        #TODO add categories, subplaces, nameswaps...
        days = []
        self.days.sort()

        for day in self.days:
            days.append(repr(day) + '\n')
        
        return ''.join(days)


    #CHECK IF BROKEN! NOW A PLACE CAN ONLY HAVE ONE SUPERPLACE
    def subplaces_of(self,place, recursive = True):
        """Get list of all subplaces of a place. The 'recursive' parameter
        (default True) defines whether we get only the direct subplaces of the
        entire hierarchy."""
        if place:
            if not recursive:
                return self.subplaces.get(place,[])
            else:
                tmp = self.subplaces.get(place,[])
                res = tmp
                for x in tmp:
                    res=unique(res+self.subplaces_of(x,False))
                return res
        else:
            return None


    def superplaces_of(self,place, recursive = True):
        """Get list of all places a place is subplace of. The 'recursive' parameter
        (default True) defines whether we get only the direct superplaces of the
        entire hierarchy."""
        if place:
            if not recursive:
                return self.superplaces.get(place,place)
            else:                
                tmp = self.superplaces.get(place,place)
                if tmp == place:
                    return tmp
                else:
                    return self.superplaces_of(tmp, True)
        else:
            return None


    def category_of(self,place):
        """returns the global category of a given place (None if inexistent)"""
        for c in self.categories:
            if place in self.categories[c]:
                return c
        return None


    def category_places(self,cat):
        """returns list of all the places with a given category"""
        return self.categories.get(cat,[])
    

    def all_places(self):
        """returns list of all visited places"""
        res = []
        for d in self.days:
            tmp = d.all_places()
            for k in tmp.keys():
                if not k in res:
                    res.append(k)
        return res


    def time_at_place(self, place):
        """Returns number of minutes spent at a given place"""
        res = 0
        for d in self.days:
            tmp = d.all_places()
            for k in tmp.keys():
                if k == place:
                    res+=tmp[k]
        return res


    def time_at_all_places(self):
        """All places visited. Returns dict where places are the keys and the
        value is the number of minutes spent there
        """
        res = {}
        for d in self.days:
            tmp = d.all_places()
            for k in tmp.keys():
                res[k] = res.get(k,0) + tmp[k]
        return res


    def sorted_places(self):
        """Returns list of tuples (place,minutes), sorted in ascending order
        of minutes
        """
        tmp = []
        places = self.time_at_all_places()        
        for p in places.keys():
            tmp.append((p,places[p]))
        tmp.sort((lambda x,y: cmp(x[1] ,y[1])))
        return tmp


    def coordinates_for(self,place):
        """returns [lat,lon] for a given place, if known (None otherwise)"""
        if place.lower() in self.coordinates:
            return self.coordinates[place.lower()]
        else:
            return None


    def somewhere(self, exclude_travel=True):
        """"How many minutes per day, and equivalent in days, did I stay
        somewhere (recyprocal of 'moving'). If exclude_travel=True, spans
        for "indoors travels" (ex: LIS airport -> LHR airport) are excluded
        from the total."""
        tmp = []

        for d in self.days:
            tmp.append(d.somewhere(exclude_travel))
        total = sum(tmp)
        return total, total/1440.0


    def moving(self):
        """How many minutes per day, and equivalent in days, was I moving?
           (recyprocal of 'somewhere'). """
        tmp = []

        for d in self.days:
            tmp.append(d.moving())
        total = sum(tmp)
        return total, total/1440.0


    def when_at(self, place, strict = True, recursive = False, exact_match = False):
        """Returns list of spans for when I was at a given place.
        If strict==True (default) it checks only the actual place. If it is
        False, it checks all subplaces as well. In that case, the 'recursive'
        parameter will be used to decide if we get only the direct subplaces
        or all the hierarchy"""
        res = []
        if strict:
            places = [place]
        else:
            places = unique([place]+self.subplaces_of(place,recursive))
        for d in self.days:
            for place in places:
                tmp = d.when_at(place, exact_match)
                if tmp:
                    res=res+tmp
        return res


    def where_when(self, date, time):
        """where was I at a given date ('yyyy_mm_dd') and time ('military
        format')
        """
        for d in self.days:
            if d.date==date:
                return d.where_when(time)



    def total_at(self, place, strict = True, recursive = False):
        """How many minutes was I at a given place? If strict==True (default) it
        checks only the actual place. If it is false, it checks all subplaces as
        well. In that case, the 'recursive' parameter will be used to decide if
        we get only the direct subplaces or all the hierarchy"""
        res = []
        if strict:
            places = [place]
        else:
            places = unique([place]+self.subplaces_of(place,recursive))

        total = 0
        for d in self.days:
            for place in places:
                total += d.total_at(place)
        return total


    def with_tag(self,tag,exact = True):
        """Return list of tuples (day,span) for stays with a given tag.
        If 'exact' is True (default), it looks for exact matches. Otherwise it will
        do a substring match"""
        res = []
        for d in self.days:
            if d.with_tag(tag,exact):
                res=res+[(d, d.with_tag(tag,exact))]
        return res


    def with_semantics(self,sem,exact = False):
        """Return list of tuples (day,span) for stays with given semantics.
        If 'exact' is True (default), it looks for exact matches. Otherwise it will
        do a substring match"""
        res = []
        for d in self.days:
            if d.with_semantics(sem,exact):
                res=res+[(d, d.with_semantics(sem,exact))]
        return res

    # From MySteps. Probably incomplete for the latest LIFE format...
    def to_json(self):
        """Returns JSON object that represents the LIFE file"""

        life = {
            "categories": self.categories,
            "subplaces": self.subplaces,
            "superplaces": self.superplaces,
            "nameswaps": self.nameswaps,
            "locationswaps": self.locationswaps,
            "coordinates": self.coordinates,
            "days": []
        }

        self.days.sort()
                
        for day in self.days:
            life["days"].append(day.to_json())

        return life


############################################################
#####  Day Class: the record of an entire day  #############
############################################################

class Day:
    """One day (set of spans"""
    def __init__(self, date):
        self.date = date
        self.notes = ""
        self.spans = []

    def add_span(self,span):
        """Adds a span to the day"""
        self.spans.append(span)

    def add_note(self,note):
        self.notes=self.notes+note+"\n"

    def all_places(self):
        """dictionary with keys for all places visited in the day, vith the
        values being the number of minutes there"""
        res = {}
        for s in self.spans:
            if s.multiplace():
                res[s.place[0]] = res.get(s.place[0],0)
                res[s.place[1]] = res.get(s.place[1],0)
            else:
                res[s.place] = res.get(s.place,0)+s.length()
        return res


    def __lt__(self, other):
        return self.date < other.date


    def __iter__(self):
        for s in self.spans:
            yield s


    def update_placenames(self, substs):
        for s in self.spans:
            s.update_placenames(substs)


    def somewhere(self,exclude_travel=True):
        """"How many minutes did I stay somewhere (recyprocal of 'moving').
        If exclude_travel=True, spans for "indoors travels"
        (ex: LIS airport -> LHR airport) are excluded from the total."""
        tmp = sum([x.length() for x in self.spans])
        if exclude_travel:
            return tmp-sum([x.length() for x in self.spans if x.multiplace()])
        else:
            return tmp


    def moving(self):
        """How many minutes was I moving? (recyprocal of 'somewhere'). """
        return 24*60-self.somewhere()


    def when_at(self,place, exact_match = False):
        """returns list of spans for when I was at a particular place"""
        res = []
        for s in self.spans:
            if s.when_at(place, exact_match):
                res.append(s)
        return res

    def where_when(self,time):
        """returns the name of the place I was at a give time (in 'military format')"""
        t=military_to_minutes(time)
        for s in self.spans:
            if s.start<=t<=s.end:
                return s.place
        return None

    def total_at(self,place, exact_match = False):
        """Returns total number of minutes at a given place"""
        return sum([x.length()+1 for x in self.when_at(place,exact_match)])


    def with_tag(self,tag,exact = True):
        """Returns all spans with a certain tag. If 'exact' is True (default)
        it will perform an exact match. Otherwise it will do a substring match"""
        res = []
        for s in self.spans:
            if s.has_tag(tag, exact):
                res.append(s)
        return res


    def with_semantics(self,sem,exact = True):
        """Returns all spans with certain semantics. If 'exact' is True (default)
        it will perform an exact match. Otherwise it will do a substring match"""
        res = []
        for s in self.spans:
            if s.has_semantics(sem, exact):
                res.append(s)
        return res


    #DEPRECATED?
    def reconstitute_day(self, cats = {}):
        res = []
        if self.spans[0].start != 0:
            res.append(((0,self.spans[0].start-1),"moving"))
        prev = None
        for s in self.spans:
            if prev:
                res.append(((prev,s.start),"moving"))
            res.append(((s.start,s.end),s.place))
            prev = s.end+1
        if s.end<24*60:
            res.append(((s.end+1,24*60),"moving"))
        return res


    def to_json(self):
        """Returns a JSON object that represents the day"""
        
        day = {
            "date": '--'+self.date,
            "spans": [],
            "notes": self.notes,
            "start_timezone": timezone_from_offset(self.spans[0].start_timezone) if self.spans[0].start_timezone==self.spans[0].end_timezone else None
        }
        
        for s in self.spans:
            day["spans"].append(s.to_json())

        return day



    def __repr__(self):
        tmp = "--"+self.date +"\n"
        if self.spans[0].start_timezone==self.spans[0].end_timezone:
            tmp += "%s\n" % timezone_from_offset(self.spans[0].start_timezone)
        for s in self.spans:
            tmp+=str(s)+"\n"
        return tmp





############################################################
#######  Span Class: A time-span, during a day  ############
############################################################

class Span:
    """A time-span, during which I was somewhere, within a day"""
    def __init__(self, day, start, end, place, timezone = "UTC"):
        """'start', 'end' in the "military time" format: "1543".
        'day' is the day the span is in, as "yyyy_mm_dd". 'timezone' is "UTC+4",
        etc. Timezone can be a list of two elements, and in that case the first
        will be the timezone of a multiplace start, the second of its end.
        """
        self.start = military_to_minutes(start)
        self.end = military_to_minutes(end)
        self.day = day
        self.parse_place(place)  #get place name, semantics, tags, etc.
        if "->" in self.place:
            self.place=(self.place.split("->")[0].strip(),self.place.split("->")[1].strip())
            # if a single place, store string. If 'indoors trip', add list of [start,end]
            # That will be a 'multiplace'
        if type(timezone)==list: 
            self.start_timezone=timezone_offset(timezone[0])
            self.end_timezone=timezone_offset(timezone[1])
        else:
            self.start_timezone=self.end_timezone=timezone_offset(timezone)        



    def parse_place(self,to_parse):
        """Extract tags, semantics and place name from a span in .life format"""
        acc=""
        context = ""
        self.tags=""
        self.semantics=""
        self.place=""
        for c in to_parse:
            if c=="[":
                if acc:
                    if context=="":
                        self.place=acc
                    acc=""
                context = "["
            elif c=="{":
                if acc:
                    if context=="":
                        self.place=acc
                    acc=""
                context = "{"
            elif c=="]":
                if context=="[":
                    self.tags=acc
                    context="."
                    acc=""
                else:
                    acc=acc+c
            elif c=="}":
                if context=="{":
                    self.semantics=acc
                    context="."
                    acc=""
                else:
                    acc=acc+c
            else:
                acc=acc+c
        if acc:            
            self.place=acc
        if self.tags=="":
            self.tags=[]
        else:
            self.tags=[x.strip() for x in self.tags.split("|")]
        if self.semantics=="":
            self.semantics=[]
        else:
            self.semantics=[x.strip() for x in self.semantics.split("|")]
        self.place = self.place.strip()


    def multiplace(self):
        """Return true if span contains 'indoor trip', False otherwise."""
        return type(self.place)==tuple


    def update_placenames(self, substs):
        if self.multiplace():
            self.place=(substs[self.place[0]],substs[self.place[1]])
        else:
            self.place=substs[self.place]


    def has_tag(self,tag, exact = True):
        """Returns True is span has a certain tag. If 'exact' is True (default)
        it will perform an exact match. Otherwise it will do a substring match"""
        if exact:
            return tag in self.tags
        else:
            for x in self.tags:
                if tag in x:
                    return True
            return False


    def has_semantics(self,sem, exact=True):
        """Returns True is span has certain semantics. If 'exact' is True (default)
        it will perform an exact match. Otherwise it will do a substring match"""
        if exact:
            return sem in self.semantics
        else:
            for x in self.semantics:
                if sem in x:
                    return True
            return False


    def when_at(self,place, exact_match = False):
        """Returns True if I was at a given place in this span, False otherwise."""
        if self.multiplace():
            return self.place[0]==place or self.place[1]==place or \
                   (not exact_match and (place in self.place[0] or place in self.place[0]))
        else:
            return self.place==place or \
                   (not exact_match and place in self.place)
    

    def length(self):
        """Return duration of span, in minutes"""
        return self.end - self.start



    def start_utc(self):
        """Return start time in UTC timezone in ISO format
        (eg: 2015-02-12T23:32:00Z)
        """
        x = self.start-self.start_timezone*60
        #print "|",x,"|", self.start,self.end, self.start_timezone
        if x<0:
            day = yesterday(self.day)
            x=x+60*24            
        elif x>(60*24):
            day = tomorrow(self.day)
            x=x-60*24
        else:
            day = self.day
        return well_formed_date(day,x)+"Z"


    def end_utc(self):
        """Return end time in UTC timezone in ISO format
        (eg: 2015-02-12T23:32:00Z)
        """
        x = self.end-self.end_timezone*60        
        if x<0:
            day = yesterday(self.day)
            x=x+60*24            
        elif x>(60*24):
            day = tomorrow(self.day)
            x=x-60*24
        else:
            day = self.day
        return well_formed_date(day,x)+"Z"


    def start_localtime(self):
        """Return end time in local timezone in ISO format
        (eg: 2015-02-12T23:32:00)
        """
        return well_formed_date(self.day,self.start)


    def end_localtime(self):
        """Return end time in local timezone in ISO format
        (eg: 2015-02-12T23:32:00)
        """
        return well_formed_date(self.day,end.start)

    # From MySteps. May be incomplete for the latest LIFE format...
    def to_json(self):
        """Returns a JSON object that represents the span"""

        return {
            "day": self.day,
            "start": minutes_to_military(self.start),
            "end": minutes_to_military(self.end),
            "tags": self.tags if self.tags else None,
            "semantics": self.semantics if self.semantics else None,
            "place": self.place,
            "end_timezone": timezone_from_offset(self.end_timezone) if self.start_timezone == self.end_timezone else None
        }


    def __repr__(self):
        if type(self.place)==tuple:
            place = self.place[0]+"->"+self.place[1]
        else:
            place = self.place
        if self.start_timezone == self.end_timezone:
            return minutes_to_military(self.start)+"-"+minutes_to_military(self.end)+": "+  \
                   place+" "+ \
                   ("[%s]" % "|".join(self.tags) if self.tags else "") + \
                   ("{%s}" % "|".join(self.semantics) if self.semantics else "") 
        else:
            return "@"+timezone_from_offset(self.end_timezone)+"\n"+ \
                   minutes_to_military(self.start)+"-"+minutes_to_military(self.end)+": "+  \
                   place+" "+ \
                   ("[%s]" % "|".join(self.tags) if self.tags else "") + \
                   ("{%s}" % "|".join(self.semantics) if self.semantics else "") 





if __name__=="__main__":
    l=Life("location_semantics.txt")
    for d in l:
        if "community day" in d.notes:
            print(d.date)
            
    for s in l.days[42]:
        print(s)
    print(l.days[13])
    print(l.category_of("ist"))
    print("\n")
    print(l.placename_at("pavilhão atlântico","2017-06-17"))
    print(l.current_placename("sbc fórum algarve"))
    print(l.update_to_superplaces(l.update_places(l["2011_01_22"])))
#    for d in l:
#        print(d)
