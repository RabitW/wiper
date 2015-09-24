drop database wip;
create database wip;
use wip;


create table project (
	id integer not null auto_increment,
	name varchar(100) not null unique,
	url varchar(100), 
	ip varchar(50), 
	ctime timestamp not null default CURRENT_TIMESTAMP,
	whois text,
	description text,
	primary key (id)
) engine=InnoDB  default charset=utf8;

create table host (
	id integer not null auto_increment, 
	title varchar(100),
	url varchar(100), 
	ip varchar(50),
	protocol integer not null,
	level integer not null, 
	os varchar(150), 
	server_info varchar(150),
	middleware varchar(200), 
	description text, 
	project_id integer not null,
	unique key ipurl (ip, url),
	primary key (id),
	constraint project_id_host foreign key (project_id) references project (id)
) engine=InnoDB  default charset=utf8;


create table vul (
	id integer not null auto_increment, 
	name varchar(100) not null, 
	url varchar(4096),
	info varchar(1024), 
	type integer, 
	level integer, 
	description text, 
	host_id integer not null, 
	primary key (id),
	constraint host_id_vul foreign key (host_id) references host (id)
) engine=InnoDB  default charset=utf8;


create table comment (
	id integer not null auto_increment, 
	name varchar(100) not null, 
	url varchar(4096),
	info varchar(1024), 
	level integer, 
	attachment varchar(200),
	description text, 
	host_id integer not null, 
	primary key (id),
	constraint host_id_comment foreign key (host_id) references host (id)
) engine=InnoDB  default charset=utf8;


create table tmp_host (
	id integer not null auto_increment,
	title varchar(200) not null unique,
	url varchar(100), 
	ip varchar(50),
	protocol integer not null,
	level integer,
	os varchar(150), 
	server_info varchar(150),
	middleware varchar(200),
	project_id integer not null,
	source varchar(50),
	primary key (id),
	constraint project_id_tmp foreign key (project_id) references project (id)
) engine=InnoDB  default charset=utf8;