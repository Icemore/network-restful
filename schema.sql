drop table if exists tasks;
create table tasks (
  id integer primary key autoincrement,
  date_from text not null,
  date_to text not null,
  cur_id text not null
);