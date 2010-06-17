#!/usr/bin/perl

# This only needs to be run once, but it *should* be idempotent.

# Note that *before* you do this, you have to log into MySQL with an
# admin account (typically root), create the resched database, and
# grant privileges on it to the user.  The database name, username,
# and password also must match what's in dbconfig.pl

require "./db.pl";
my $db = dbconn();

$db->prepare("use $dbconfig::database")->execute();
$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     resched_alias (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          alias mediumtext, canon mediumtext)"
    )->execute();

$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     resched_bookings (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          resource integer,
          bookedfor longtext,
          bookedby integer,
          fromtime datetime,
          until datetime,
          doneearly datetime,
          followedby integer,
          isfollowup integer,
          staffinitials tinytext,
          latestart datetime,
          notes longtext,
          tsmod timestamp
     )"
    )->execute();


$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     resched_resources (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          name mediumtext,
          schedule integer,
          switchwith tinytext,
          showwith tinytext,
          combine tinytext,
          requireinitials integer,
          requirenotes integer,
          autoex integer,
          flags tinytext
     )"
    )->execute();


$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     resched_schedules (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          name tinytext,
          firsttime datetime,
          intervalmins integer,
          durationmins integer,
          durationlock integer,
          intervallock integer,
          booknow integer,
          alwaysbooknow integer
     )"
    )->execute();


$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     authcookies (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          cookiestring mediumtext,
          user integer,
          restrictip tinytext,
          expires datetime
     )"
    )->execute();

$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     users (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          username   tinytext,
          hashedpass tinytext,
          fullname   mediumtext,
          nickname   mediumtext,
          prefs      mediumtext
     )"
    )->execute();

$db->prepare(
    "CREATE TABLE IF NOT EXISTS
     misc_variables (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          namespace  tinytext,
          name       mediumtext,
          value      longtext
     )"
    )->execute();

$db->prepare(
    "CREATE TABLE IF NOT EXISTS
    auth_by_ip (
          id integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
          ip tinytext,
          user integer
    )"
    )->execute();

