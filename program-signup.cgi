#!/usr/bin/perl -T
# -*- cperl -*-

our $debug = 0;
$maxrows = 150; # safety precaution
our $didyoumean_enabled = 1;

$ENV{PATH}='';
$ENV{ENV}='';

use DateTime;
use DateTime::Span;
use HTML::Entities qw(); sub encode_entities{ my $x = HTML::Entities::encode_entities(shift@_);
                                              $x =~ s/[-][-]/&mdash;/g;
                                              return $x; }
use Data::Dumper;

require "./forminput.pl";
require "./include.pl";
require "./auth.pl";
require "./db.pl";
require "./ajax.pl";
require "./datetime-extensions.pl";

our %input = %{getforminput()};
our $persistentvars = qq[usestyle=$input{usestyle}&amp;useajax=$input{useajax}];
our $hiddenpersist  = qq[<input type="hidden" name="usestyle" value="$input{usestyle}" />\n  <input type="hidden" name="useajax" value="$input{useajax}" />];

sub usersidebar; # Defined below.

my $ab = authbox(sub { my $x = getrecord('users', shift); "<!-- Hello, $$x{nickname} -->"; });

my %categoryflag = (
                    'D' => ['D', 'Default',         'This is the default category for new programs.'],
                    'L' => ['L', 'Library program', 'Programs in this category are our official programs.', 'inherited'],
                    'T' => ['T', 'Third-party',     'Programs in this party are unofficial or run by a third party.', 'inherited'],
                    'X' => ['X', 'Obsolete',        'This category is no longer used for new programs.'],
                    '#' => ['#', 'DEBUG',           'Programs in this category are not real programs.  They exist only for testing the booking software.', 'inherited'],
                   );
my %programflag = (
                   'L' => ['L', 'Library program', 'This is one of our official programs.'],
                   'T' => ['T', 'Third-party',     'This program is unofficial or is run by a third party.'],
                   'X' => ['X', 'Canceled',        'This program has been canceled.'],
                   '#' => ['#', 'DEBUG',           'This is not a real program.  It exists only for testing the booking software.', 'inherited'],
                  );
my %signupflag = (
                  'X' => ['X', 'Canceled', 'This person no longer plans to attend.'],
                  '?' => ['?', 'Maybe',    'This person is unsure whether they will attend.'],
                  '#' => ['#', 'DEBUG',    'You can ignore this signup: we were just testing the booking software.']
                 );

sub respondtouser { # This is the non-AJAX way.
  my ($content, $title) = @_;
  $content or die "No content.";
  $title ||= 'Program Signup';
  print include::standardoutput($title, $content, $ab, $input{usestyle});
  exit 0;
}

if ($auth::user) {
  if ($input{action} eq 'newprogram') {
    respondtouser(programform(undef), "Create New Program");
  } elsif ($input{action} eq 'createprogram') {
    respondtouser(createprogram());
  } elsif ($input{action} eq 'editprogram') {
    respondtouser(programform(getrecord('resched_program', $input{program})));
  } elsif ($input{action} eq 'updateprogram') {
    respondtouser(updateprogram());
  } elsif ($input{action} eq 'showprogram') {
    my $progtitle = "Program Signup";
    my $prog = getrecord('resched_program', $input{program});
    if (ref $prog) {
      $progtitle = "Program Signup - $$prog{title}";
    }
    respondtouser(showprogram(), $progtitle);
  } elsif ($input{action} eq 'dosignup') {
    respondtouser(dosignup(), "Program Signup");
  } elsif ($input{action} eq 'editsignup') {
    respondtouser(editsignup(), "Edit Program Signup");
  } elsif ($input{action} eq 'updatesignup') {
    respondtouser(updatesignup(), "Edit Program Signup");
  } elsif ($input{action} eq 'AjaxAddSignup') {
    my $num = $input{numofnewsignups} + 1;
    sendresponse(ajaxvarupdate('numofnewsignups', $num)
                 . ajaxtoggledisplay('addmoresignupsbutton', 'inline')
                 . ajaxtoggledisplay('onemomentnoticegoeshere', 'none')
                 . ajaxinsert('insertemptysignupshere',
                              blankattender($num) # both content and focus
                             )
                );
  } else {
    respondtouser(listprograms(), "Upcoming Programs");
  }
} else {
  respondtouser(qq[You probably need to log in.], "Not Authorized");
}

sub dateform {
  my ($dt, $nameprefix, $idprefix, $timeonly) = @_;
  $nameprefix ||= '';
  $idprefix   ||= $nameprefix;
  my @monthoption = map { my $m = $_;
                          my $sel = ($m == $dt->month()) ? ' selected="selected"' : '';
                          qq[<option value="$m"$sel>$monthname{$m}</option>]# . "\n                 "
                        } 1 .. 12;
  my $houroptions = include::houroptions($dt->hour());
  my $timeform = qq[<select id="${idprefix}hour" name="${nameprefix}hour">$houroptions</select> :
                   <input type="text" id="${idprefix}minute" name="${nameprefix}minute" size="3" value="] . (sprintf "%02d", $dt->minute()) . qq[" />];
  return $timeform if $timeonly;
  return qq[<input type="text" id="${idprefix}year"  name="${nameprefix}year"  value="] . $dt->year() . qq[" size="5" />
             <select id="${idprefix}month" name="${nameprefix}month">@monthoption</select>
             <input type="text" id="${idprefix}day" name="${nameprefix}day" size="3" value="] . $dt->mday() . qq[" />
             <nobr>at $timeform</nobr>]
}

sub programform {
  my ($record) = @_;
  my ($categoryform, $untilform, $startdateform, $hidden);
  my @category   = grep { not ($$_{flags} =~ /X/) } getrecord('resched_program_category');
  my %category   = map { $$_{id} => $$_{category} } @category;
  my @defaultcategory = map { $$_{id} } grep { $$_{flags} =~ /D/ } @category;
  #use Data::Dumper; warn Dumper(+{ category_array => \@category, category_hash  => \%category, default        => \@defaultcategory,  });
  if (ref $record) {
    $categoryform  = include::optionlist('category', \%category, $$record{category});
    $startdateform = dateform(DateTime::From::MySQL($$record{starttime}), 'start');
    $untilform     = dateform(DateTime::From::MySQL($$record{endtime}), 'end');
    $savebutton    = 'Save Changes';
    $hidden        = qq[<input type="hidden" name="action" value="updateprogram" />
    <input type="hidden" name="program" value="$$record{id}" />];
  } else {
    $categoryform  = include::optionlist('category', \%category, $defaultcategory[0], 'newprogramcategory');
    my $startdate = DateTime->now(time_zone => $include::localtimezone)->add(months => 1);
    $startdateform = dateform($startdate, 'start');
    $untilform     = dateform($startdate, 'end', undef, 'timeonly');
    $savebutton    = 'Create This Program';
    $hidden        = qq[<input type="hidden" name="action" value="createprogram" />];
    $record = +{# Defaults for new programs:
                agegroup => '',
                title    => '',
               };
  }
  return qq[<form action="program-signup.cgi" method="post">\n  $hiddenpersist
  $hidden
  <table class="dbrecord">
     <tr><th><label for="category">Category</label></th>
         <td>$categoryform</td></tr>
     <tr><th><label for="title">Program Title:</label></th>
         <td><input type="text" id="newprogramtitle" name="title" size="30" value="$$record{title}" /></td>
         <td class="explan">(You can use the same title repeatedly if the date or time is different.)</td></tr>
     <tr><th><label for="agegroup">Age Group:</label></th>
         <td><input type="text" id="newprogramagegroup" name="agegroup" size="10" value="$$record{agegroup}" /></td>
         <td class="explan">(The computer doesn't know what the age group means; it's just for our reference.)</td></tr>
     <tr><th><label for="startyear">Date:</label></th>
         <td>$startdateform</td></tr>
     <tr><th><label for="endhour">Until:</label></th>
         <td>$untilform</td></tr>
     <!-- TODO: Checkboxes for flags. -->
  </table>
  <input type="submit" value="$savebutton" />
</form>];
}

#sub blanknewprogramform {
#  return programform(undef);
#}

#sub editprogram {
#  return programform(getrecord('resched_program', $input{program}));
#}

sub updateprogram {
  my $prog = getrecord('resched_program', $input{program});
  if (not ref $prog) {
    return qq[<div class="error"><div><strong>Error</strong></div>
       Something is wrong.  I was unable to find program number $input{program} in the database.</div>]
  } else {
    my ($when)  = assembledatetime('start', \%input, $include::localtimezone, 'cleanup');
    my ($until) = assembledatetime('end',   \%input, $include::localtimezone, 'cleanup');
    if ($until < $when) {
      $until = $when->clone()->add( hours => 1);
    }
    $$prog{starttime}  = DateTime::Format::ForDB($when);
    $$prog{endtime}    = DateTime::Format::ForDB($until);
    my ($catid)        = $input{category} =~ /(\d+)/;
    my $category       = getrecord('resched_program_category', $catid);
    if (ref $category) {
      $$prog{category} = $catid;
    }
    # TODO: Flags
    my @change = @{updaterecord('resched_program', $prog)};
    return programform(getrecord('resched_program', $$prog{id}));
  }
}

sub updatesignup {
  my ($id) = ($input{id} =~ m/(\d+)/);
  my $s = getrecord('resched_program_signup', $id);
  if (not ref $s) {
    return qq[<div class="error"><div><strong>Error</strong></div>
       Unfortunately, I was not able to find signup record $id in the database.</div>];
  } else {
    $$s{attender} = (encode_entities($input{attender}) || $$s{attender});
    $$s{phone}    = (encode_entities($input{phone})    || $$s{phone});
    $$s{flags}    = join '', map { $input{"flag" . $_} ? $_ : '' } keys %signupflag;
    $$s{comments} = (encode_entities($input{comments}) || $$s{comments});
    my @change = @{updaterecord('resched_program_signup', $s)};
    return editsignup();
  }
}

sub editsignup {
  my ($id) = ($input{id} =~ m/(\d+)/);
  my $s = getrecord('resched_program_signup', $id);
  if (not ref $s) {
    return qq[<div class="error"><div><strong>Error</strong></div>
       Unfortunately, I was not able to find signup record $id in the database.</div>];
  } else {
    my $flagcheckboxes = flagcheckboxes($$s{flags}, \%signupflag);
    return qq[<form action="program-signup.cgi" method="post">\n  $hiddenpersist
    <input type="hidden" name="action" value="updatesignup" />
    <input type="hidden" name="id"     value="$id" />
    <table class="dbrecord">
       <tr><th><label for="attender">Name:</label></th>
           <td><input id="attender" name="attender" type="text" size="35" value="$$s{attender}" /></td></tr>
       <tr><th><label for="phone">Phone:</label></th>
           <td><input id="phone" name="phone" type="text" size="20" value="$$s{phone}" /></td></tr>
       <tr><th><label>Flags:</label></th>
           <td>$flagcheckboxes
           </td></tr>
       <tr><th><label for="comments">Comments:</label></th>
           <td><textarea id="comments" name="comments" rows="5" cols="35">$$s{comments}</textarea></td></tr>
    </table>
    <input type="submit" value="Save Changes" />
   </form>];
  }
}

sub blankattender {
  my ($num) = @_;
  my $html = qq[      <tr>
        <td> </td><td><input type="text" id="signup${num}attender" name="signup${num}attender" size="30" /></td>
                   <td><input type="text" id="signup${num}phone"    name="signup${num}phone"    size="15" /></td>
                   <td><!-- TODO:  Checkboxes --></td>
                   <td><textarea id="signup${num}comments" name="signup${num}comments" rows="3" cols="25"></textarea></td>
      </tr>\n];
  if (wantarray) {
    return ($html, "signup${num}attender");
  } else {
    return $html;
  }
}

sub createprogram {
  my ($when) = assembledatetime('start', \%input, $include::localtimezone, 'cleanup');
  my $until = $when->clone()->set( hour => $input{endhour}, minute => $input{endminute});
  if ($until < $when) {
    $until = $when->clone()->add( hours => 1);
  }
  my ($catid) = $input{category} =~ /(\d+)/;
  $catid += 0;
  my $category = getrecord('resched_program_category', $catid);
  if (ref $category) {
    my $flags = join '', map { $$_[0] } grep { $$_[3] eq 'inherited' } values %categoryflag;
    my $newprogram = +{
                       category  => $catid,
                       title     => encode_entities($input{title}),
                       agegroup  => encode_entities($input{agegroup}),
                       starttime => DateTime::Format::ForDB($when),
                       endtime   => DateTime::Format::ForDB($until),
                      };
    my $result = addrecord('resched_program', $newprogram);
    if ($result) {
      $input{program} = $db::added_record_id;
      return ((qq[<div class="info"><div><strong>Program Created</strong></div>
  Here is the signup sheet for your new program:</div>]
               . dosignup()), "Program Created: $newprogramtitle");
    } else {
      return qq[<div class="error"><div><strong>Error</strong></div>
                Something went wrong when attempting to add your new program to the database.
                It may not have been successfully added.
                <!-- DBI says: $DBI::errstr --></div>]
    }
  } else {
    return qq[<div class="error"><div><strong>Error</strong></div>
       I tried to find category $catid in the database, but I could not find it.
       I am not programed to create a program with an unknown category.</div>]
  }
}

sub dosignup {
  my ($progid) = $input{program};
  my @result;
  my $prog = getrecord('resched_program', $id);
  if ($prog) {
    for my $n (1 .. ($input{numofnewsignups} || 1)) {
      my $attender = encode_entities($input{"signup" . $n . "attender"});
      my $phone    = encode_entities($input{"signup" . $n . "phone"});
      # TODO: Handle Flags
      my $comments = encode_entities($input{"signup" . $n . "comments"});
      if ($attender) {
        my $category = getrecord('resched_program_category', $$prog{category});
        push @result, addrecord("resched_program_signup",
                                +{
                                  program_id => $progid,
                                  attender   => $attender,
                                  phone      => $phone,
                                  comments   => $comments,
                                  flags      => inheritflags($$category{flags}, \%categoryflag),
                                 });
      }}
    return showprogram();
  } else {
    return qq[<div class="error"><div><strong>Error:</strong></div>
     I cannot seem to find any record of program number $id in the database.</div>];
  }
}

sub inheritflags {
  my ($sourceflags, $flaghash) = @_;
  my $flags  = '';
  for my $f (split //, $sourceflags) {
    my $fr = $$flaghash{$f};
    if (ref $fr) {
      my ($char, $name, $description, $inherited) = @$fr;
      if (defined $inherited and ($inherited eq 'inherited')) {
        $flags .= $char;
      }}}
  return $flags;
}

sub showprogram {
  my ($id) = $input{program};
  my $prog = getrecord('resched_program', $id);
  my $when = include::datewithtwelvehourtime(DateTime::From::MySQL($$prog{starttime}));
  my $cancelednote = '<!-- no canceled signups -->';
  if ($prog) {
    my @signup = sort { $$a{id} <=> $$b{id} } findrecord('resched_program_signup', 'program_id', $id);
    if (not $input{showcanceled}) {
      my @c = grep { $$_{flags} =~ /X/ } @signup;
      if (scalar @c) {
        my $number  = scalar @c;
        my $were    = include::inflectverbfornumber($number, 'was', 'were');
        my $npeople = include::sgorpl($number, 'person', 'people');
        my $have    = include::inflectverbfornumber($number, 'has', 'have');
        my $ncancel = include::sgorpl($number, 'cancelation');
        $cancelednote = qq[<div class="info">There $were also $npeople previously
           signed up for this program who $have since canceled.
           <a href="program-signup.cgi?action=showprogram&amp;program=$id&amp;showcanceled=yes&amp;$persistentvars">Click here to show a list that includes the $ncancel.</a></div>];
        @signup = grep { not ($$_{flags} =~ /X/) } @signup;
      }
    }
    my $num = 1;
    my $category = getrecord('resched_program_category', $$prog{category});
    for my $i (0 .. $#signup) {
      $signup[$i]{num} = $num++;
    }
    @signup = sortbylastname(@signup);
    my $howmany = $input{showcanceled}
      ? qq[Altogether there have been $num people signed up for this program.]
      : qq[There are currently $num people signed up for this program.];
    return qq[
<div style=" text-align: center; font-size: 1.2em; ">
  <div id="programtitle"><strong>$$prog{title}, $when</strong></div>
  <div id="agegroupandcategory">
       <span class="programagegroup">for $$prog{agegroup}</span>
       <span class="programcategory">(category: $$category{category})</span></div>
  <div id="programtotal">$howmany</div>
</div>
<form action="program-signup.cgi" method="post">\n  $hiddenpersist
    <input type="hidden" name="program" value="$id" />
    <input type="hidden" name="action" value="dosignup" />
    <input type="hidden" name="dummyvar" value="thisdoesnothing" />
    <table class="table signupsheet"><thead>
      <tr><td>#</td><td>Attender</td><td>Phone</td><td>Flags</td><td>Comments</td></tr>
    </thead><tbody>
      ].(join "\n", map {
        my $s = $_;
        my $flags = showflags($$s{flags}, \%signupflag);
        qq[<tr class="signup"><td>$$s{num}</td><td><a href="program-signup.cgi?action=editsignup&amp;id=$$s{id}&amp;$persistentvars">$$s{attender}</a></td><td>$$s{phone}</td><td>$flags</td><td>$$s{comments}</td></tr>]
      } @signup)
        . blankattender(1)
        . ($input{useajax} eq 'off' ? '' : qq[
      <tr id="insertemptysignupshere">
        <td colspan="4"><input type="hidden" id="numofnewsignups" name="numofnewsignups" value="1" />
                        <span id="onemomentnoticegoeshere"><span id="onemomentnotice" style="display: none;">One moment...</span></span>
                        <input type="button" id="addmoresignupsbutton" value="Add More" onclick="augmentprogramsignupform();" /></td>
       </tr>]) . qq[
    </tbody></table>
    <input type="submit" value="Submit" />
    </form>\n$cancelednote\n
    <div class="wholeprogramactions"><a class="button" href="program-signup.cgi?action=editprogram&amp;program=$$prog{id}&amp;$persistentvars">Edit Program Details</a></div>];
  } else {
    return qq[<div class="error"><div><strong>Error:</strong></div>
     I cannot seem to find any record of program number $id in the database.</div>];
  }
}

sub flagcheckboxes {
  my ($flags, $flaghash, $prefix) = @_;
  $flaghash ||= \%signupflag;
  $prefix   ||= 'flag';
  my @f = map {
    my ($char, $name, $description, $inherit) = @{$$flaghash{$_}};
    my $checked = ($flags =~ /[$char]/) ? ' checked="checked"' : '';
    my $lcname = lc $name;
    qq[<nobr><input id="cb$prefix$lcname" type="checkbox" name="$prefix$char"$checked />
                     <label for="cb$prefix$lcname"><span class="flagchar">$char</span> - </label><span class="flagname"><abbr title="$description">$name</abbr></span></nobr>]
  } sort {
    $a cmp $b
  } keys %$flaghash;
  return join ' ', @f;
}

sub showflags {
  my ($flags, $flaghash) = @_;
  $flaghash ||= \%signupflag;
  my @f = map {
    my $f = $_;
    my ($char, $name, $description, $inherit) = @{$$flaghash{$f}};
    qq[<abbr title="$description" class="flag"><nobr><span class="flagchar">$char</span> - <span class="flagname">$name</span></nobr></abbr>]
  } split //, $flags;
  return join '', @f;
}

sub sortbylastname {
  return map {
    #my ($r, $s) = 
    $$_[0]
    #  , $$_[1]; $$r{flags} = $s;
    #$r;
  } sort {
    $$a[1] cmp $$b[1]
  } map {
    my $rec = $_;
    my ($last, $rest, $sortby);
    if ($$rec{attender} =~ /,/) {
      # If it's got a comma in it, assume it's already in surname-first order.
      $sortby = $$rec{attender};
    } else {
      ($rest, $last) = $$rec{attender} =~ /^(.*?)\s*(\w+)\s*$/;
      $sortby = "$last, $rest";
    }
    #use Data::Dumper; warn Dumper(+{ rec => $rec, sortby => $sortby });
    [ $rec, $sortby ];
  } @_;
}

sub listprograms {
  my @program = getprogramlist(100);
  my $programlist = join "\n       ", map {
    my $prec  = $_;
    my $title = encode_entities($$prec{title});
    my $dt    = DateTime::From::MySQL($$prec{starttime});
    my $when  = include::datewithtwelvehourtime($dt);
    my $dow   = $dt->day_name();
    my $ages  = $$prec{agegroup};
    qq[<li><a href="program-signup.cgi?action=showprogram&amp;program=$$prec{id}&amp;$persistentvars" title="$when">$title</a>
           for $ages, $dow, $when</li>]
  } @program;
  return qq[<div><strong>Upcoming Programs:</strong></div><ul>$programlist</ul>];
}

sub getprogramlist {
  my ($maxprogs) = @_;
  # TODO: use parameters to do things like allow showing old programs
  $maxprogs = 12 if $maxprogs < 1;
  my @program = grep { not $$_{flags} =~ /X/
                     } sort {
                       $$a{starttime} cmp $$b{starttime}
                         or $$a{endtime} cmp $$b{endtime}
                           or $$a{id} cmp $$b{id}
                     } getsince('resched_program', 'starttime', DateTime->now(time_zone => $include::localtimezone));
  if ($maxprogs < scalar @program) {
    @program = @program[ 0 .. ($maxprogs - 1)];
  }
  return @program;
}

sub usersidebar {
  my @program = getprogramlist(getvariable('resched', 'max_sidebar_programs'));
  my $programlist = join "\n       ", map {
    my $prec     = $_;
    my $title    = encode_entities($$prec{title});
    my $dt       = DateTime::From::MySQL($$prec{starttime});
    my $when     = include::datewithtwelvehourtime($dt);
    my $showdate = getvariable('resched', 'sidebar_programs_showdate') ? (' ' . $dt->month_abbr() . '&nbsp;' . $dt->mday()) : '';
    my $showtime = getvariable('resched', 'sidebar_programs_showtime') ? (' ' . include::twelvehourtimefromdt($dt)) : '';
    qq[<li><a href="program-signup.cgi?action=showprogram&amp;program=$$prec{id}&amp;$persistentvars" title="$when">$title$showdate$showtime</a></li>]
  } @program;
  my @rescat = include::categories();
  my $resourcestoday = qq[<div><strong><span onclick="toggledisplay('todaysectionlist','todaysectionmark');" id="todaysectionmark" class="expmark">-</span>
      <span onclick="toggledisplay('todaysectionlist','todaysectionmark','expand');">Today's Bookings:</span></strong>
   <div id="todaysectionlist"><ul>
      ] . (join "\n      ", map {
        my ($catname, @id) = @$_;
        qq[<li><a href="./?view=] . (join ',', @id)
        . qq[&amp;$persistentvars&amp;magicdate=today">$catname</a></li>]
      } @rescat) . qq[   </ul></div></div>];
  my $stylesection = include::sidebarstylesection('', 'program-signup.cgi');
  return qq[<div class="sidebar">
   <div><strong>Program Signup:</strong><ul>
       <li><a href="program-signup.cgi?action=newprogram&amp;$persistentvars">Create New Program</a></li>
       $programlist
       <li><a href="program-signup.cgi?action=listprograms&amp;$persistentvars">List Programs</a></li>
     </ul></div>
   $resourcestoday
   $stylesection
</div>]
}
