#!/usr/bin/perl -T
# -*- cperl -*-

$ENV{PATH}='';
$ENV{ENV}='';

require "./forminput.pl";
require "./include.pl";
require "./auth.pl";

our %input = %{getforminput()};
my $ab = authbox(sub { my $x = getrecord('users', shift); "<!-- Hello, $$x{nickname} -->"; });

my %resflag = (
               R => ['R', 'Room', 'This resource is a meeting room.'],
               X => ['X', 'eXclude', 'Exclude this resource from sidebar lists.'],
               requireinitials => [ undef, 'Initials',   'Staff must enter initials when booking this resource.'],
               requirenotes    => [ undef, 'Notes',      'Staff must enter certain notes when booking this resource.'],
               autoex          => [ undef, 'AutoExtend', 'Bookings for this resource are automatically extended in certain cases.'],
              );
my %schflag = (
               durationlock    => [ undef, 'DurationLock',  ''],
               intervallock    => [ undef, 'IntervalLock',  ''],
               booknow         => [ undef, 'BookNow',       ''],
               alwaysbooknow   => [ undef, 'AlwaysBookNow', ''],
              );

if ($auth::user) {
  my $user = getrecord('users', $auth::user);
  ref $user or die "Unable to retrieve user record for $auth::user";
  if ($$user{flags} =~ /A/) {
    my $notice = '';
    my $title = "resched administration";
    if ($input{action} eq 'reslist') {
      ($notice, $title) = reslist();
    } elsif ($input{action} eq 'schlist') {
      ($notice, $title) = schlist();
    } elsif (($input{action} eq 'resedit') or ($input{action} eq 'resnew')) {
      ($notice, $title) = resform();
    } elsif (($input{action} eq 'schedit') or ($input{action} eq 'schnew')) {
      ($notice, $title) = schform();
    } elsif ($input{action} eq 'updateresource') {
      ($notice, $title) = resupdate();
    } elsif ($input{action} eq 'createresource') {
      ($notice, $title) = rescreate();
    } elsif ($input{action} eq 'updateschedule') {
      ($notice, $title) = schupdate();
    } elsif ($input{action} eq 'createschedule') {
      ($notice, $title) = schcreate();
    } else {
      $notice = qq[<p>Welcome to the resource scheduling administration interface.</p>]
    }
    print include::standardoutput($title,
                                  $notice,
                                  $ab, $input{usestyle});
  } else {
    print include::standardoutput('Administrative Access Needed',
                                  "<p>In order to access this page you need to log into an account that has the Administrator flag set.</p>",
                                  $ab, $input{usestyle});
  }
} else {
  print include::standardoutput('Authentication Needed',
                                "<p>In order to access this page you need to log in.</p>",
                                $ab, $input{usestyle});
}

sub reslist {
  my @r = getrecord('resched_resources');
  my @row = map {
    my $r = $_;
    my $s = getrecord('resched_schedules', $$r{schedule});
    my $flags = join ', ', map { my $f = $resflag{$_};
                                 my $prefix = $$f[0] ? qq[$$f[0] - ] : '';
                                 qq[<abbr title="$$f[2]">$prefix$$f[1]</abbr>]
                               } ((split //, $$r{flags}),
                                  (grep { $$r{$_} } qw(requireinitials requirenotes autoex)));
    qq[<tr><td><a href="admin.cgi?action=resedit&amp;resource=$$r{id}">$$r{name}</a></td>
           <td><a href="admin.cgi?action=schedit&amp;schedule=$$r{schedule}">$$s{name}</a></td>
           <td>$$r{switchwith}</td><td>$$r{showwith}</td><td>$$r{combine}</td>
           <td>$flags</td></tr>]
  } @r;
  return (qq[
  <table class="table list" id="resourcelist"><thead>
     <tr><th>Resource</th><th>Schedule</th><th>Switch With</th><th>Show With</th><th>Combine With</th><th>Flags and Such</th></tr>
  </thead><tbody>
     ] . (join "\n     ", @row) . qq[</tbody></table>
  ], 'List of Resources - resched');
}

sub resform {
  my ($res, $saveword, $editword, $action);
  if ($input{resource} || $input{id}) {
    $res = getrecord('resched_resources', $input{resource} || $input{id});
    ($saveword, $editword, $action) = ('Save Changes', 'Edit Resource', 'updateresource');
  } else {
    my ($name) = 'Untitled1'; while (findrecord('resched_resources', 'name', $name)) { $name++ }
    $res = +{ name => $name };
    $saveword = $editword = 'Create Resource';
    $action = 'createresource';
  }
  my $idfield = $$res{id} ? qq[\n     <input type="hidden" name="id" value="$$res{id}" />] : '';
  my $flagcheckboxes = join "\n               ", map {
    my $f = $_;
    qq[<div><input  id="cbflag$f" name="flag$f" type="checkbox"]
                . (($$res{flags} =~ "$f") ? ' checked="checked"' : '') . qq[ />
            <label for="cbflag$f" title="$resflag{$f}[2]">$resflag{$f}[1]</label></div>]
  } sort { $a cmp $b } grep { /^.$/ } keys %resflag;
  return (qq[<form id="resourceform" action="admin.cgi" method="post">
     <input type="hidden" name="action" value="$action" />$idfield
     <table><tbody>
       <tr><th><label for="name">Resource Name</label></th>
           <td><input  id="name" name="name" type="text" size="40" value="$$res{name}" /></td>
           <td>Human-readable name for the resource.</td></tr>
       <tr><th><label for="schedule">Schedule</label></th>
           <td>] . include::optionlist('schedule', +{ map { $$_{id} => $$_{name} } getrecord('resched_schedules')
                                           }, $$res{schedule}) . qq[</td>
           <td>See the <a href="admin.cgi?action=schlist">list of schedules</a>
               or <a href="admin.cgi?action=schnew">create a new one</a>.</td></tr>
       <tr><th><label for="switchwith">Switch With</label></th>
           <td><input  id="switchwith" name="switchwith" type="text" size="20" value="$$res{switchwith}" /></td>
           <td>If you leave this blank, the first category containing the resource will be used.</td></tr>
       <tr><th><label for="showwith">Show With</label></th>
           <td><input  id="showwith" name="showwith" type="text" size="20" value="$$res{showwith}" /></td>
           <td>If you leave this blank, the first category containing the resource will be used.</td></tr>
       <tr><th><label for="combine">Combine With</label></th>
           <td><input  id="combine" name="combine" type="text" size="20" value="$$res{combine}" /></td>
           <!-- td>If you leave this blank, the first category containing the resource will be used.</td --></tr>
       <tr><th>Flags and Such</th>
           <td><div><input  id="requireinitials" name="requireinitials" type="checkbox"] . ($$res{requireinitials} ? ' checked="checked"' : '') . qq[ />
                    <label for="requireinitials" title="$resflag{requireinitials}[2]">Require Initials</label></div>
               <div><input  id="requirenotes" name="requirenotes" type="checkbox"] . ($$res{requirenotes} ? ' checked="checked"' : '') . qq[ />
                    <label for="requirenotes" title="$resflag{requirenotes}[2]">Require Notes</label></div>
               <div><input  id="autoex" name="autoex" type="checkbox"] . ($$res{autoex} ? ' checked="checked"' : '') . qq[ />
                    <label for="autoex" title="$resflag{autoex}[2]">Auto-Extend</label></div>
               $flagcheckboxes
           </td></tr>
     </tbody></table>
     <input type="Submit" value="$saveword" />
  </form>], qq[$editword]);
}

sub resupdate {
  my $res = getrecord('resched_resources', $input{id});
  ref $res or return (include::errordiv('Missing Resource Record', qq[I am unable to locate a resource record for resource $input{id}.]), 'Missing Resource Record');
  $$res{name} = encode_entities($input{name});
  my $sch = getrecord('resched_schedules', $input{schedule});
  $$res{schedule} = $$sch{id} if ref $sch;
  $$res{$_} = encode_entities($input{$_}) for qw(switchwith showwith combine);
  $$res{$_} = ($input{$_} ? 1 : 0) for qw(requireinitials requirenotes autoex);
  $$res{flags} = join '', sort { $a cmp $b } grep { $input{'flag' . $_} } grep { /^.$/ } keys %resflag;
  updaterecord('resched_resources', $res);
  return resform();
}

sub rescreate {
  my $sch = getrecord('resched_schedules', $input{schedule});
  ref $sch or return (include::errordiv('Error: Missing Schedule', qq[I cannot find a schedule record for schedule $input{schedule} (and every resource must be assigned to a valid schedule).]), 'Error');
  my $res = +{ name            => encode_entities($input{name}),
               schedule        => $$sch{id},
               switchwith      => encode_entities($input{switchwith}),
               showwith        => encode_entities($input{showwith}),
               combine         => encode_entities($input{combine}),
               flags           => (join '', sort { $a cmp $b } grep { $input{'flag' . $_} } grep { /^.$/ } keys %resflag),
             };
  $$res{$_} = ($input{$_} ? 1 : 0) for qw(requireinitials requirenotes autoex);
  my (@dupe) = findrecord('resched_resources', 'name', $$res{name});
  if (scalar @dupe) {
    my $detail = (1 == scalar @dupe) ? qq! (<a href="admin.cgi?action=resedit&amp;resource=${$dupe[0]}{id}">resource ${$dupe[0]}{id}</a>) ! : '';
    return (include::errordiv('Duplicate Resource Name', 'There ' . include::isare(scalar @dupe) . ' already ' . include::sgorpl((scalar @dupe), 'resource') . qq[ called <q>$$res{name}</q>. $detail If you really want to have multiple resources with the same name, you should set allow_duplicate_names in <a href="config.cgi">config.cgi</a>.]),
            'Duplicate Resource Name')
      unless getvariable('resched', 'allow_duplicate_names');
  }
  my $result = addrecord('resched_resources', $res);
  $input{id} = $db::added_record_id;
  return resform();
}

sub schlist {
  my @s = getrecord('resched_schedules');
  my @row = map {
    my $s = $_;
    my $flags = join ', ', map { my $f = $schflag{$_};
                                 my $prefix = $$f[0] ? qq[$$f[0] - ] : '';
                                 qq[<abbr title="$$f[2]">$prefix$$f[1]</abbr>]
                               } ((split //, $$s{flags}),
                                  (grep { $$s{$_} } qw(durationlock intervallock booknow alwaysbooknow)));
    my $firsttime = include::twelvehourtimefromdt(DateTime::From::MySQL($$s{firsttime}));
    qq[<tr><td><a href="admin.cgi?action=schedit&amp;schedule=$$s{id}">$$s{name}</a></td>
           <td>$firsttime</td><td>$$s{intervalmins}</td><td>$$s{durationmins}</td><td>$flags</td></tr>]
  } @s;
  return qq[
  <table class="table list" id ="schedulelist"><thead>
     <tr><th>Schedule</th><th>First Timeslot</th><th>Interval (minutes)</th><th>Duration (minutes)</th><th>Flags and Such</th></tr>
  </thead><tbody>
     ] . (join "\n     ", @row) . qq[
  </tbody></table>], 'List of Schedules - resched';
}

sub schform {
  my ($sch, $saveword, $editword, $action);
  my $now     = DateTime->now( time_zone => $include::localtimezone );
  my %ot      = include::openingtimes();
  my $firstot = (sort { $ot{$a}[0] <=> $ot{$b}[0] or $ot{$a}[1] <=> $ot{$b}[1] } keys %ot)[0];
  if ($input{schedule} || $input{id}) {
    $sch = getrecord('resched_schedules', $input{schedule} || $input{id});
    ($saveword, $editword, $action) = ('Save Changes', 'Edit Schedule', 'updateschedule');
  } else {
    my ($name)  = 'Unnamed1'; while (findrecord('resched_schedules', 'name', $name)) { $name++; }
    my $dt      = DateTime->new( time_zone => $include::localtimezone,
                                 year      => $now->year(),
                                 month     => $now->month(),
                                 day       => 1,
                                 hour      => $ot{$firstot}[0],
                                 minute    => $ot{$firstot}[1],
                               );
    $sch = +{
             name          => $name,
             intervalmins  => 15,
             durationmins  => 60,
             intervallock  => 1,
             booknow       => 1,
             alwaysbooknow => 1,
             firsttime     => DateTime::Format::ForDB($dt),
            };
    $saveword = $editword = 'Create Schedule';
    $action = 'createschedule';
  }
  my $idfield = $$sch{id} ? qq[\n     <input type="hidden" name="id" value="$$sch{id}" />] : '';
  my $ftdt    = DateTime::From::MySQL($$sch{firsttime});
  my %ft      = ( year => $ftdt->year(), month => $ftdt->month(), day => $ftdt->mday(), hour => $ftdt->hour(), minute => $ftdt->minute() );
  return (qq[<form id="scheduleform" action="admin.cgi" method="post">
     <input type="hidden" name="action" value="$action" />$idfield
     <!-- There's no point in bothering the user about intervallock, booknow, or alwaysbooknow, since they currently are not actually checked; the software just assumes they're always turned on. -->
     <input type="hidden" name="intervallock"  value="$$sch{intervallock}" />
     <input type="hidden" name="booknow"       value="$$sch{booknow}" />
     <input type="hidden" name="alwaysbooknow" value="$$sch{alwaysbooknow}" />
     <table><tbody>
       <tr><th><label for="schname">Name</label></th>
           <td><input  id="schname" name="name" size="40" value="$$sch{name}" /></td>
           <td>Human-readable name for this schedule, so you can easily keep track of which is which.</td></tr>
       <tr><th><label for="firsttimehour">First Timeslot</label></th>
           <td><select id="firsttimehour" name="firsttimehour">] . ( include::houroptions($ft{hour}, $firstot) ) . qq[</select>
               <input  id="firsttimeminute" name="firsttimeminute" size="3" value="$ft{minute}" />
               <input type="hidden" name="firsttimeyear"  value="$ft{year}" />
               <input type="hidden" name="firsttimemonth" value="$ft{month}" />
               <input type="hidden" name="firsttimeday"   value="$ft{day}" />
               </td>
           <td>The earliest time in the morning that resources on this schedule can ever be booked.
               (If the hour you want is not available, check your openingtimes in <a href="config.cgi">config.cgi</a>.)</td></tr>
       <tr><th><label for="intervalmins">Booking Interval</label></th>
           <td><input  id="intervalmins" name="intervalmins" size="4" value="$$sch{intervalmins}" /></td>
           <td>Booking slots will be available starting every this many minutes; e.g., if you set
               this to 30 your booking timeslots will all be aligned to the half hour.</td></tr>
       <tr><th><label for="durationmins">Booking Duration</label></th>
           <td><input  id="durationmins" name="durationmins" size="4" value="$$sch{durationmins}" /></td>
           <td>Bookings will usually be for this many minutes.
               This number <strong>must</strong> be a multiple of the booking interval, for technical reasons.
               For example, if your booking interval is 15, your booking duration could be 15 or 30 or 45 or 60, etc.</td></tr>
       <tr><th><label for="durationlock">Duration Lock</label></th>
           <td><input  id="durationlock" name="durationlock" type="checkbox"]
                     . ($$sch{durationlock} ? ' checked="checked"' : '') . qq[ />
                     <label for="durationlock">Lock Duration</label></td>
           <td>If set, all bookings will be created for the amount of time specified by the booking duration.
               (The form will not provide the option of changing the ending time when the booking is created.
                The <q>extend booking</q> and <q>done early</q> features are still available.)
               This is particularly useful if the booking interval and booking duration are equal.</td></tr>
     </tbody></table>
     <input type="submit" value="$saveword" />
  </form>], $editword);
}
sub schupdate {
  my $sch = getrecord('resched_schedules', $input{id});
  ref $sch or return (include::errordiv('Missing Schedule Record', qq[I am unable to locate a schedule record for schedule $input{id}.]), 'Missing Schedule Record');
  $$sch{name} = encode_entities($input{name});
  $$sch{$_}        = $input{$_} ? 1 : 0 for qw(intervallock durationlock booknow alwaysbooknow);
  ($$sch{$_})      = $input{$_} =~ /(\d+)/ for qw(intervalmins durationmins);
  $$sch{firsttime} = assembledatetime( 'firsttime', \%input, $include::localtimezone );
  return include::errordiv('Invalid Booking Duration', 'The booking duration must be a multiple of the booking interval.', 'Invalid Booking Duration')
    if $$sch{durationmins} % $$sch{intervalmins};
  my @dupe = grep { $$_{id} ne $$sch{id} } findrecord('resched_schedules', 'name', $$sch{name});
  if (scalar @dupe) {
    my $detail = (1 == scalar @dupe) ? qq! (<a href="admin.cgi?action=schedit&amp;schedule=${$dupe[0]}{id}">schedule ${$dupe[0]}{id}</a>) ! : '';
    return (include::errordiv('Duplicate Schedule Name', 'There ' . include::isare(scalar @dupe) . ' already ' . include::sgorpl((scalar @dupe), 'schedule') . qq[ called <q>$$sch{name}</q>. $detail If you really want to have multiple schedules with the same name, you should set allow_duplicate_names in <a href="config.cgi">config.cgi</a>.]),
            'Duplicate Schedule Name') unless getvariable('resched', 'allow_duplicate_names');
  }
  updaterecord('resched_schedules', $sch);
  return schform();
}
sub schcreate {
  my $sch = +{ name         => encode_entities($input{name}), };
  $$sch{$_}        = $input{$_} ? 1 : 0 for qw(intervallock durationlock booknow alwaysbooknow);
  ($$sch{$_})      = $input{$_} =~ /(\d+)/ for qw(intervalmins durationmins);
  $$sch{firsttime} = assembledatetime( 'firsttime', \%input, $include::localtimezone );
  return include::errordiv('Invalid Booking Duration', 'The booking duration must be a multiple of the booking interval.', 'Invalid Booking Duration')
    if $$sch{durationmins} % $$sch{intervalmins};
  my @dupe = findrecord('resched_schedules', 'name', $$sch{name});
  if (scalar @dupe) {
    my $detail = (1 == scalar @dupe) ? qq! (<a href="admin.cgi?action=schedit&amp;schedule=${$dupe[0]}{id}">schedule ${$dupe[0]}{id}</a>) ! : '';
    return (include::errordiv('Duplicate Schedule Name', 'There ' . isare(scalar @dupe) . ' already ' . sgorpl((scalar @dupe), 'schedule') . qq[ called <q>$$sch{name}</q>. $detail If you really want to have multiple schedules with the same name, you should set allow_duplicate_names in <a href="config.cgi">config.cgi</a>.]),
            'Duplicate Schedule Name') unless getvariable('resched', 'allow_duplicate_names');
  }
  my $result = addrecord('resched_schedules', $sch);
  $input{id} = $db::added_record_id;
  return schform();
}

sub usersidebar {
  return qq[
  <div class="sidebar">
     <div><div><strong><span onclick="toggledisplay('sbreslist','sbresmark');" id="sbresmark" class="expmark">-</span>
                       <span onclick="toggledisplay('sbreslist','sbresmark','expand');">Resources:</span></strong></div>
          <div id="sbreslist"><ul>
             <li><a href="admin.cgi?action=reslist">List Existing</a></li>
             <li><a href="admin.cgi?action=resnew">Create New</a></li>
             </ul></div>
          </div>
     <div><div><strong><span onclick="toggledisplay('sbschlist','sbschmark');" id="sbschmark" class="expmark">-</span>
                       <span onclick="toggledisplay('sbschlist','sbschmark','expand');">Schedules:</span></strong></div>
          <div id="sbschlist"><ul>
             <li><a href="admin.cgi?action=schlist">List Existing</a></li>
             <li><a href="admin.cgi?action=schnew">Create New</a></li>
             </ul></div>
          </div>
     <div><div><strong><span onclick="toggledisplay('sbusrlist','sbusrmark');" id="sbusrmark" class="expmark">+</span>
                       <span onclick="toggledisplay('sbusrlist','sbusrmark','expand');">Users:</span></strong></div>
          <div id="sbusrlist" style="display: none;"><ul>
             <li>List Existing</li>
             <li>Create New</li>
             </ul></div>
          </div>
     <div><div><strong><span onclick="toggledisplay('sbipalist','sbipamark');" id="sbipamark" class="expmark">+</span>
                       <span onclick="toggledisplay('sbipalist','sbipamark','expand');">IP Auth:</span></strong></div>
          <div id="sbipalist" style="display: none;"><ul>
             <li>List IP Auth Records</li>
             <li>Create New IP Auth</li>
             </ul></div>
          </div>
     <div><div><strong><span onclick="toggledisplay('sbmsclist','sbmscmark');" id="sbmscmark" class="expmark">-</span>
                       <span onclick="toggledisplay('sbmsclist','sbmscmark','expand');">Miscellany:</span></strong></div>
          <div id="sbipalist"><ul>
             <li><a href="config.cgi">Configure site-wide variables</a></li>
             </ul></div>
          </div>
     <div><a href="index.cgi">Return to the index.</a></div>
  </div>];
}
