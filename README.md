# thesis_tools
All files related to creation and loading of TIN data structures.

Construction and loading of TIN structures into the database is done by lastools availble at http://www.cs.unc.edu/~isenburg/lastools/ . which is piped to custom Python tools available here. A distinction is made between single type loaders, which output only one triangle or star at the time, while multi type loaders output collections of geometries in buckets, such as MultiPolygons. 

Original lastools Python parsers are adapted from https://github.com/tudelft3d/streamingstars

## Construction Multi

A typical way of constructing the the multistar data structure and loading it into the database is: 

```BASH
/* Construct quadtree buckets information */
spfinalize -i rijswijk.laz -ilas -o -v -level 5 -ospb | spdelaunay2d -
ispb -osmb | python qtfin.py 5
/* Create data structure based on the previous run */
spfinalize -i rijswijk.laz -ilas -o -v -level 5 -ospb | spdelaunay2d -
ispb -osmb | python multistar.py 5
```

Both the spfinalize and spdelaunay2d are lastools programs that use streaming algorithms. The first run uses a Python script qtfin.py that collects statistics about the number of points for each bucket. This information is reused by all the multi type data structures to create the buckets in the database. The second step uses a Python postgresql client to load the data
into the database. These script could be sped up by using COPY instead of INSERT statements.

## Construction Single

Single type features are run as follows:

```BASH
/* Create pgTIN data structure */
spfinalize -i rijswijk.laz -ilas -o -v -level 5 -ospb | spdelaunay2d -ispb -osmb | python pgtin.py > pipe
```

The named pipe can then be used as follows:

```SQL 
CREATE TABLE points (id int, x double precision, y double precision, z double precision, star integer[]);
COPY points from ’pipe’;
ALTER table points add primary key (id);
```

