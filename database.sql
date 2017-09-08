create database blog;

use blog;

GRANT ALL PRIVILEGES
ON demo_app.*
TO 'admin'@'%'
IDENTIFIED BY 'password';

CREATE TABLE entry (
	id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL,
	slug VARCHAR(255) NOT NULL, 
	content TEXT NOT NULL,
	published INTEGER NOT NULL,
	timestamp DATETIME NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX entry_slug ON entry(slug);
CREATE INDEX entry_published ON entry(published);
CREATE INDEX entry_timestamp ON entry(timestamp);

CREATE TABLE ftsentry (
	entry_id INTEGER,
	content TEXT NOT NULL
);
CREATE TABLE ftsentry_content (
	docid INTEGER PRIMARY KEY
);


CREATE TABLE ftsentry_segments (
	blockid INTEGER PRIMARY KEY, 
	block BLOB
);
CREATE TABLE ftsentry_segdir (
	level INTEGER,
	idx INTEGER,
	start_block INTEGER,
	leaves_end_block INTEGER,
	end_block INTEGER,
	root BLOB,
	PRIMARY KEY(level, idx)
);
CREATE TABLE ftsentry_docsize (
	docid INTEGER PRIMARY KEY, 
	size BLOB
);
CREATE TABLE ftsentry_stat (
	id INTEGER PRIMARY KEY,
	value BLOB
);