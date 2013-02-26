# $Id: mysqlclient14.rs.spec 92 2007-01-12 17:12:25Z wdierkes $
#
# Rackspace Managed Hosting
# Contact: BJ Dierkes <wdierkes@rackspace.com>
#


# Setting initial dist defaults.  Do not modify these.
# Note: Mock sets these up... but we need to default for manual builds.
%{!?el3:%define el3 0}
%{!?el4:%define el4 0}
%{!?el5:%define el5 0}
%{!?rhel:%define rhel 'empty'}

# Build Options
#
# In order to properly build you will likely need to add one of the following
# build options:
#
#       --with el3
#       --with el4
#       --with el5
#
#
# Note for maintainers/builders: mock handles all these defs.  We include them 
# here for manual builds.
#
%{?_with_el3:%define el3 1}
%{?_with_el3:%define rhel 3}
%{?_with_el3:%define dist .el3}

%{?_with_el4:%define el4 1}
%{?_with_el4:%define rhel 4}
%{?_with_el4:%define dist .el4}

%{?_with_el5:%define el5 1}
%{?_with_el5:%define rhel 5}
%{?_with_el5:%define dist .el5}


# build with cluster by default, but not RHEL3
%if %{el3}
# do nothing... 
%else
%define _with_cluster 1
%endif

%define with_cluster %{?_with_cluster:1}%{!?_with_cluster:0}

Name: mysqlclient15
Version: 5.0.92
Release: 3.ius%{?dist}
Summary: Backlevel MySQL shared libraries.
License: GPL
Group: Applications/Databases
URL: http://www.mysql.com

Source0: http://dev.mysql.com/get/Downloads/MySQL-4.1/mysql-%{version}.tar.gz
Source4: scriptstub.c
Source5: my_config.h
Patch201: mysql-5.0.27-libdir.patch
Patch2: mysql-errno.patch
Patch303: mysql-5.0.33-libtool.patch
Patch304: mysql-5.0.37-testing.patch
Patch205: mysql-5.0.27-no-atomic.patch
Patch6: mysql-rpl_ddl.patch
Patch7: mysql-rpl-test.patch
Patch207: mysql-5.0.41-compress-test.patch
Patch208: mysql-5.0.67-mysqld_safe.patch
Patch209: mysql-5.0.67-bindir.patch
Patch217: mysql-5.0.75-automake_el3.patch
Patch317: mysql-strmov.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-root
Prereq: /sbin/ldconfig, /sbin/install-info, grep, fileutils, chkconfig
BuildRequires: gperf, perl, readline-devel, openssl-devel
BuildRequires: gcc-c++, ncurses-devel, zlib-devel
BuildRequires: libtool automake autoconf gcc
Requires: bash
Provides: libmysqlclient.so.15   libmysqlclient.so.15.0.0 
Provides: libmysqlclient_r.so.15 libmysqlclient_r.so.15.0.0

%if %{el5}
BuildRequires: libpcap
Requires: libpcap
%endif

%if %{el3}
BuildRequires: gettext
%else
BuildRequires: gettext-devel
%endif


# Working around perl dependency checking bug in rpm FTTB. Remove later.
%define __perl_requires %{SOURCE999}

# Force include and library files into a nonstandard place
%{expand: %%define _origincludedir %{_includedir}}
%{expand: %%define _origlibdir %{_libdir}}
%define _includedir %{_origincludedir}/mysql5
%define _libdir %{_origlibdir}/mysql5

%description
This package contains backlevel versions of the MySQL client libraries
for use with applications linked against them.  These shared libraries
were created using MySQL %{version}.

%package devel

Summary: Backlevel files for development of MySQL applications.
License: GPL
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}

%description devel
This package contains the libraries and header files that are needed for
developing MySQL applications using backlevel client libraries.

%prep
%setup -q -n mysql-%{version}

%patch201 -p1
%patch2 -p1
%patch303 -p1
%patch304 -p1
%patch205 -p1
%patch6 -p1
%patch7 -p1
%patch207 -p1
%patch208 -p1
%patch209 -p1
%patch217 -p1 -b .openssl
%patch317 -p1 -b .strmov

# Work around for missing mkinstalldirs 
#if [ ! -e mkinstalldirs ]; then
#  cp -a /usr/share/gettext/mkinstalldirs mkinstalldirs
#  chmod +x mkinstalldirs
#fi

libtoolize --force
aclocal
automake

# This is a hack to fix autoconf issues on Rhel3
%if %{el3}
echo "ifdef([m4_pattern_allow], [m4_pattern_allow([AS_HELP_STRING])])" >> aclocal.m4
%endif

autoconf
autoheader

%build
CFLAGS="%{optflags} -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE"
%if %{el3}
CFLAGS="$CFLAGS -fno-strict-aliasing"
%else
CFLAGS="$CFLAGS -fno-strict-aliasing -fwrapv"
%endif

# Also Resolved MySQL Bug: #18091 and #19999
# same as MySQL builds... always build as
# position indipendant code.
CFLAGS="$CFLAGS -fPIC"

CXXFLAGS="$CFLAGS  -felide-constructors -fno-rtti -fno-exceptions"
export CFLAGS CXXFLAGS

%configure \
	--with-readline \
	--with-vio \
	--with-openssl \
	--without-debug \
	--enable-shared \
	--without-bench \
	--localstatedir=/var/lib/mysql \
	--with-unix-socket-path=/var/lib/mysql/mysql.sock \
	--with-mysqld-user="mysql" \
	--with-extra-charsets=all \
	--enable-local-infile \
	--enable-large-files=yes --enable-largefile=yes \
	--enable-thread-safe-client \
	--disable-dependency-tracking \
	--with-archive-storage-engine \
	--with-federated-storage-engine \
	--with-blackhole-storage-engine \
	--with-csv-storage-engine \
	%{?_with_cluster:--with-extra-charsets=all} \
	%{?_with_cluster:--with-ndbcluster} \
	--with-named-thread-libs="-lpthread"

gcc $CFLAGS $LDFLAGS -o scriptstub "-DLIBDIR=\"%{_libdir}/mysql\"" %{SOURCE4}

make %{?_smp_mflags}
make check

%install
rm -rf %{buildroot}

%makeinstall

install -m 644 include/my_config.h %{buildroot}%{_includedir}/mysql/my_config_`uname -i`.h
install -m 644 %{SOURCE5} %{buildroot}%{_includedir}/mysql/

mv %{buildroot}%{_bindir}/mysqlbug %{buildroot}%{_libdir}/mysql/mysqlbug
install -m 0755 scriptstub %{buildroot}%{_bindir}/mysqlbug
mv %{buildroot}%{_bindir}/mysql_config %{buildroot}%{_libdir}/mysql/mysql_config
install -m 0755 scriptstub %{buildroot}%{_bindir}/mysql_config

# We want the .so files both in regular _libdir (for execution) and
# in special _libdir/mysql5 directory (for convenient building of clients).
# The ones in the latter directory should be just symlinks though.
mkdir -p %{buildroot}%{_origlibdir}/mysql
pushd %{buildroot}%{_origlibdir}/mysql
mv -f %{buildroot}%{_libdir}/mysql/libmysqlclient.so.15.*.* .
mv -f %{buildroot}%{_libdir}/mysql/libmysqlclient_r.so.15.*.* .
cp -p -d %{buildroot}%{_libdir}/mysql/libmysqlclient*.so.* .
popd
pushd %{buildroot}%{_libdir}/mysql
ln -s ../../mysql/libmysqlclient.so.15.*.* .
ln -s ../../mysql/libmysqlclient_r.so.15.*.* .
popd

# Put the config script into special libdir
cp -p %{buildroot}%{_bindir}/mysql_config %{buildroot}%{_libdir}/mysql

rm -rf %{buildroot}%{_prefix}/mysql-test
rm -f %{buildroot}%{_libdir}/mysql/*.a
rm -f %{buildroot}%{_libdir}/mysql/*.la
rm -rf %{buildroot}%{_datadir}/mysql
rm -rf %{buildroot}%{_bindir}
rm -rf %{buildroot}%{_libexecdir}
rm -rf %{buildroot}%{_infodir}/*
rm -rf %{buildroot}%{_mandir}/man1/*
rm -rf %{buildroot}%{_mandir}/man8/*
rm -f %{buildroot}%{_origlibdir}/mysql5/mysql/libmysqlclient.so
rm -f %{buildroot}%{_origlibdir}/mysql5/mysql/libmysqlclient_r.so
rm -f %{buildroot}%{_origlibdir}/mysql5/mysql/libndbclient.so
rm -f %{buildroot}%{_origlibdir}/mysql5/mysql/libndbclient.so.2

mkdir -p %{buildroot}/etc/ld.so.conf.d
echo "%{_origlibdir}/mysql" > %{buildroot}/etc/ld.so.conf.d/%{name}-%{_arch}.conf

%clean
rm -rf %{buildroot}

%post 
%if %{el3}
  if ! grep '^%{_libdir}/mysql$' /etc/ld.so.conf > /dev/null 2>&1
  then
    echo "%{_libdir}/mysql" >> /etc/ld.so.conf
  fi
%endif
/sbin/ldconfig


%postun
if [ $1 = 0 ] ; then
  %if %{el3}
    if grep '^%{_libdir}/mysql$' /etc/ld.so.conf > /dev/null 2>&1
    then
        grep -v '^%{_libdir}/mysql$' /etc/ld.so.conf \
            > /etc/ld.so.conf.$$ 2> /dev/null
        mv /etc/ld.so.conf.$$ /etc/ld.so.conf
    fi
  %endif
  /sbin/ldconfig
fi

%files
%defattr(-,root,root)
%doc README COPYING
%{_origlibdir}/mysql5/mysql/mysqlbug
%{_origlibdir}/mysql/libmysqlclient*15*
%{_origlibdir}/mysql5/mysql/libmysqlclient*15*
%{_origlibdir}/mysql5/mysql/mysql_config
/etc/ld.so.conf.d/mysqlclient15-*.conf 

%if %{with_cluster}
%{_origlibdir}/mysql5/mysql/libndbclient.so.2.0.0
%endif

%files devel
%defattr(-,root,root)
%{_includedir}/mysql/*.h

%if %{with_cluster}
%{_includedir}/mysql/ndb/*.h
%{_includedir}/mysql/ndb/*/*.h
%{_includedir}/mysql/ndb/*/*.hpp
%endif


%changelog
* Thu Sep 06 2012 Jeffrey Ness <jeffrey.ness@rackspace.com> - 5.0.92-3.ius
- Adding mysql-strmov.patch per LP#1046974

* Wed Sep 28 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> - 5.0.92-2.ius
- Removing mkinstalldirs

* Mon Mar 28 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> - 5.0.92-1.ius
- Latest sources from upstream
- Removed EXCEPTIONS-CLIENT from doc

* Mon Jun 14 2010 BJ Dierkes <wdierkes@rackspace.com> - 5.0.91-1.ius
- Latest sources from upstream

* Tue Jan 05 2010 BJ Dierkes <wdierkes@rackspace.com> - 5.0.89-1.ius
- Latest sources from upstream, resolves LP#499202

* Wed Oct 01 2009 BJ Dierkes <wdierkes@rackspace.com> - 5.0.85-1.ius
- Latest sources from upstream
- Rebuilding for EL4/EL5

* Mon Aug 24 2009 BJ Dierkes <wdierkes@rackspace.com> - 5.0.84-1.ius
- Latest sources from upstream

* Mon Jul 27 2009 BJ Dierkes <wdierkes@rackspace.com> - 5.0.83-1.ius
- Rebuilding for IUS.

* Tue Jun 23 2009 BJ Dierkes <wdierkes@rackspace.com> - 5.0.83-1.rs
- Latet sources from upstream.
- Removed Patch218: mysql-5.0.75-openssl.patch
- Removed Patch219: mysql-5.0.75-bug42037.patch

* Mon Mar 23 2009 BJ Dierkes <wdierkes@rackspace.com> - 5.0.77-1.rs
- Latest sources from upstream
- Added Patch208: mysql-5.0.67-mysqld_safe.patch
- Added Patch209: mysql-5.0.67-bindir.patch
- Added Patch217: mysql-5.0.75-automake_el3.patch
- Added Patch218: mysql-5.0.75-openssl.patch
- Added Patch219: mysql-5.0.75-bug42037.patch 

* Thu Nov 20 2008 BJ Dierkes <wdierkes@rackspace.com> - 5.0.67-1.rs
- Latest sources from upstream
- Added -felide-constructors to CXXFLAGS
- BuildRequires/Requires: libpcap (el5)
- BuildRequires: gcc
- Removed Patch12: mysql-5.0.51-CVE-2007-5925.patch (applied upstream).
- Removed Patch212: mysql-5.0.51-openssl-connect.patch (applied upstream).
- Removed Patch215: mysql-5.0.51-disabled-tests.patch (applied upstream).
- Removed Patch216: mysql-5.0.51a-order-by.patch (applied upstream).
 
* Sat May 17 2008 BJ Dierkes <wdierkes@rackspace.com> - 5.0.51a-1.rs
- Updating to latest sources
- Removing Patch210: mysql-5.0.45-bug29898.patch (applied upstream)
- Removing Patch209: mysql-5.0.45-disabled-tests.patch
- Adding Patch12: mysql-5.0.51-CVE-2007-5925.patch
- Adding Patch212: mysql-5.0.51-openssl-connect.patch (Resolves Bug #33050)
- Adding Patch215: mysql-5.0.51-disabled-tests.patch
- Adding Patch216: mysql-5.0.51a-order-by.patch resolves MySQL Bug #32202
  as well as Rackspace Bug [#291].
- el3 BuildRequires gettext, else BuildRequires gettext-devel.

* Wed Nov 07 2007 BJ Dierkes <wdierkes@rackspace.com> - 5.0.45-2.rs
- Adding post/postun scripts to properly handle ld.so.conf on EL3.
  Resolves Bug [#207] Improper addition of library path to ld.so.conf

* Wed Oct 24 2007 BJ Dierkes <wdierkes@rackspace.com> - 5.0.45-1.rs
- Building for MySQL5 based off of mysqlclient14 spec.
- Add -fPIC to CFLAGS
- Adding Patch201: mysql-5.0.27-libdir.patch
- Adding Patch2: mysql-errno.patch
- Adding Patch303: mysql-5.0.33-libtool.patch
- Adding Patch304: mysql-5.0.37-testing.patch
- Adding Patch205: mysql-5.0.27-no-atomic.patch
- Adding Patch6: mysql-rpl_ddl.patch
- Adding Patch7: mysql-rpl-test.patch
- Adding Patch207: mysql-5.0.41-compress-test.patch
- Adding Patch209: mysql-5.0.45-disabled-tests.patch
- Adding Patch210: mysql-5.0.45-bug29898.patch
- Adding work around for missing mkinstalldirs on rhel3.
- Adding work around for missing AS_HELP_STRING on rhel3.

* Mon Feb 05 2007 BJ Dierkes <wdierkes@rackspace.com> - 4.1.22-1.2.rs
- Removing file from man dir (conflicts with mysql-5.X packages)

* Fri Jan 12 2007 BJ Dierkes <wdierkes@rackspace.com> - 4.1.22-1.1.rs
- Fixed /etc/ld.so.conf.d/mysqlclient14-*.conf in %files
 
* Thu Jan 11 2007 BJ Dierkes <wdierkes@rackspace.com> - 4.1.22-1.rs
- Upping to latest sources
- Replaced RedHat Patch1: mysql-libdir.patch with Patch201: mysql-4.1.22-libdir.patch
- Replaced RedHat Patch3: mysql-libtool.patch with Patch203: mysql-4.1.22-libtool.patch
- Replaced RedHat Patch5: mysql-no-atomic.patch with Patch205: mysql-4.1.22-no-atomic.patch
- Replaced RedHat Patch7: mysql-test-ssl.patch with Patch207: mysql-4.1.22-test-ssl.patch  
- Removed RedHat Patch6: mysql-lock-ssl.patch (previously applied in source) 
- Removed '-fwrapv' from $CFLAGS on rhel3 
- Cleaned up %files list

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 4.1.14-4.2.1
- rebuild

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 4.1.14-4.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 4.1.14-4.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Dec 15 2005 Tom Lane <tgl@redhat.com> 4.1.14-4
- fix my_config.h for 64-bit and ppc platforms

* Wed Dec 14 2005 Tom Lane <tgl@redhat.com> 4.1.14-3
- oops, looks like we want uname -i not uname -m

* Wed Dec 14 2005 Tom Lane <tgl@redhat.com> 4.1.14-2
- Make my_config.h architecture-independent for multilib installs;
  put the original my_config.h into my_config_$ARCH.h
- Add license info (COPYING, EXCEPTIONS-CLIENT) to the shipped documentation
- Add -fwrapv to CFLAGS so that gcc 4.1 doesn't break it

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Thu Nov  3 2005 Tom Lane <tgl@redhat.com> 4.1.14-1
- created based on latest FC-4 package and mysqlclient10 specfile
