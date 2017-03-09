WikiRacer:
-----------
WikiRacer implemented makes use of BFS(Breadth First Search) to traverse
Wikipedia. BFS can be used to find shortest path in a given graph. BFS 
works across breadth of the graph moving from one layer to the next. 
BFS makes use of queue to process nodes in horizontal fashion. 
This implementation makes use of API provided by Wikipedia

How to run:
-----------

```
./wikiracer.py '{
"start":"https://en.wikipedia.org/wiki/Malaria",
"end":"https://en.wikipedia.org/wiki/Geophysics"
}'
```

Introduction:
-------------
WikiRacer implemented makes use of BFS(Breadth First Search) to traverse
Wikipedia. BFS can be used to find shortest path in a given graph. BFS 
works across breadth of the graph moving from one layer to the next. 
BFS makes use of queue to process nodes in horizontal fashion. 
This implementation makes use of API provided by Wikipedia instead of 
parsing the page using BeautifulSoup. While trying to use BeautifulSoup 
I found that parsing page is too slow and much faster way was to use API.

In this implementation BFS has couple of optimizations. When BFS visits 
a node(or wiki page) all links are cached in 'link_cache' dictionary. 
I saw that the performance of BFS improved dramatically from 240 minutes 
to 18 minutes(for first result in Result section) by using 'link_cache'. 
But the downside of 'link_cache' is that BFS makes use of more than 1G of RAM.

The other optimization is fetching of links for nodes in path is done 
parallely using  concurrent.futures module. ProcessPoolExecutor is used to 
spawn pool of worker processes which handles fetching links of 'n' nodes(pages) 
parallely. 

The worst case algorithmic complexity of BFS is O(V + E) where V is number of 
vertices(nodes) and E is the number of edges(links) in graph.

In this implementation only Python3.5 standard libraries are used. There are no 
dependancies.

The WikiRacer works for all the tests inputs that I have tried.

Results:
---------
Below are the results on Ubuntu 16.04.2 LTS VM with 4 cores and 4GB RAM.
The first example takes around 18 minutes. Rest of the examples few seconds 
to few minutes.

```
rkadam@rkadam-vbox:~/github/wikiracer$ ./wikiracer.py '{
"start":"https://en.wikipedia.org/wiki/Malaria",
"end":"https://en.wikipedia.org/wiki/Geophysics"
}'

{
    "start": "https://en.wikipedia.org/wiki/Malaria",
    "end": "https://en.wikipedia.org/wiki/Geophysics",
    "path": [
        "https://en.wikipedia.org/Malaria",
        "https://en.wikipedia.org/Agriculture",
        "https://en.wikipedia.org/M._King_Hubbert",
        "https://en.wikipedia.org/Geophysics"
    ]
}
```
```
rkadam@rkadam-vbox:~/github/wikiracer$ ./wikiracer.py '{
"start":"https://en.wikipedia.org/wiki/India",
"end":"https://en.wikipedia.org/wiki/Japan"
}'
{
    "start": "https://en.wikipedia.org/wiki/India",
    "end": "https://en.wikipedia.org/wiki/Japan",
    "path": [
        "https://en.wikipedia.org/India",
        "https://en.wikipedia.org/18th_SAARC_summit",
        "https://en.wikipedia.org/Japan"
    ]
}
```
```
rkadam@rkadam-vbox:~/github/wikiracer$ ./wikiracer.py '{
"start":"https://en.wikipedia.org/wiki/Apple",
"end":"https://en.wikipedia.org/wiki/Zebra"
}'
{
    "start": "https://en.wikipedia.org/wiki/Apple",
    "end": "https://en.wikipedia.org/wiki/Zebra",
    "path": [
        "https://en.wikipedia.org/Apple",
        "https://en.wikipedia.org/Adam_and_Eve",
        "https://en.wikipedia.org/La_Biblia_en_pasta",
        "https://en.wikipedia.org/Zebra"
    ]
}
```
```
rkadam@rkadam-vbox:~/github/wikiracer$ ./wikiracer.py '{
"start":"https://en.wikipedia.org/wiki/Computer",
"end":"https://en.wikipedia.org/wiki/Moon"
}'
{
    "start": "https://en.wikipedia.org/wiki/Computer",
    "end": "https://en.wikipedia.org/wiki/Moon",
    "path": [
        "https://en.wikipedia.org/Computer",
        "https://en.wikipedia.org/Antikythera_mechanism",
        "https://en.wikipedia.org/Moon"
    ]
}
```
```
rkadam@rkadam-vbox:~/github/wikiracer$ ./wikiracer.py '{
"start":"https://en.wikipedia.org/wiki/Google",
"end":"https://en.wikipedia.org/wiki/Mars"
}'
{
    "start": "https://en.wikipedia.org/wiki/Google",
    "end": "https://en.wikipedia.org/wiki/Mars",
    "path": [
        "https://en.wikipedia.org/Google",
        "https://en.wikipedia.org/Daily_Mail",
        "https://en.wikipedia.org/Mars"
    ]
}
```

Improvements:
-------------
1. BFS has been implemented as generator which finds all possible paths 
   between start and end url. It can be extended to find shortest path
   (Provided there is 'sufficient' memory). I tried find all BFS paths 
   for first example in results and the program ran out of memory.
2. Parallel fetch of links can be moved into separate and generic 
   ParallelExecutor class for future needs.
3. 'fetch_page_links' method of WikiApi class needs to handle wiki pages 
   with more than 500 links.
