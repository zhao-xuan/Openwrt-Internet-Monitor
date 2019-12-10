var active_device_id;
var active_since = 3600 * 12;
var interval_by = 1;
var device_list;

var ctx = document.getElementById('myChart');
var chart = new Chart(ctx, {
    type: 'bar',
    data: {
    },
    options: {
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    displayFormats: {
                        quarter: 'MMM YYYY'
                    }
                },
                stacked: true
            }],
            yAxes: [{
                stacked: true
            }]
        }
    }
});

fetch('/devices').then(
    function (response) {
        if (response.status !== 200) {
            console.log('Looks like there was a problem. Status Code: ' +
                response.status);
            return;
        }

        response.json().then(function (data) {
            device_list = data["devices"];

            var device_ul = $('#deviceList')
            device_list.forEach((value, index) => {
                var li = $('<li/>')
                    .addClass('nav-item')
                    .appendTo(device_ul);
                var a = $('<a/>')
                    .addClass('nav-link')
                    .attr('id', 'device' + value.id)
                    .attr("href", "javascript:void(0);")
                    .attr("data-device-id", value.id)
                    .text(value.name)
                    .appendTo(li);
            })
            $('[data-device-id]:first').addClass("active");

            $('[data-device-id]').click(function (event) {
                $("[data-device-id]").removeClass("active");
                var id_selected = $(event.target).attr("data-device-id");
                $(event.target).addClass("active");

                active_device_id = parseInt(id_selected);
                update(active_device_id, active_since, interval_by);
            });

            active_device_id = device_list[0].id;
            
            update(active_device_id, active_since, interval_by, function() {
                showArchive(-1, -1, -1);
            });
        })
    }
)

function getStats(device_id, view_since, interval_by, cbk) {
    fetch('/viewSince?view_since=' + view_since + '&device_id=' + device_id + '&interval_by=' + interval_by)
        .then(
            function (response) {
                if (response.status !== 200) {
                    console.log('Looks like there was a problem. Status Code: ' +
                        response.status);
                    return;
                }
                response.json().then(function (data) {
                    var stats_temp = data["stats"]
                    cbk(stats_temp);
                });
            }
        )
        .catch(function (err) {
            console.log('Fetch Error :-S', err);
        });
}


function update(device_id, view_since, interval_by, cbk) {
    getStats(device_id, view_since, interval_by, function (stats) {
        renderDeviceStats(stats);
        if (cbk) {
            cbk();
        }
    });
    
}

function renderDeviceStats(stats) {
    chart.data.datasets = [{
        label: 'Download',
        data: stats.map((item) => ({
            x: new Date(item.timestamp * 1000),
            y: Math.trunc(item.download / 1024 / 10.24) / 100
        })),
        borderWidth: 1,
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)'
    }, {
        label: 'Upload',
        data: stats.map((item) => ({
            x: new Date(item.timestamp * 1000),
            y: -Math.trunc(item.upload / 1024 / 10.24) / 100
        })),
        borderWidth: 1,
        backgroundColor: 'rgba(30, 120, 150, 0.2)',
        borderColor: 'rgba(30, 120, 150, 1)'
    }];
    chart.update();
}

function renameDevice() {
    var newname = $('#newNameInput').val();
    if (newname == "") {
        alert("Please enter a valid device name!")
        return
    }

    formData = new FormData();
    formData.append('device_id', active_device_id);
    formData.append('newname', newname);
    fetch('/rename', {
        method: "POST",
        body: formData
    }).then(() => {
        $("#device" + active_device_id).text(newname);
    })
}

$('[data-view-since]').click(function (event) {
    $("[data-view-since]").removeClass("active");
    var temp = $(event.target).attr("data-view-since");
    $(event.target).addClass("active");

    if (temp == 6 || temp == 12) {
        $('#groupByIntervalRange').attr('min', '0');
        $('#groupByIntervalRange').attr('max', '3');
        $('#groupByIntervalRange').attr('value', '0');
    } else if (temp == 24) {
        $('#groupByIntervalRange').attr('min', '1');
        $('#groupByIntervalRange').attr('max', '3');
        $('#groupByIntervalRange').attr('value', '1');
    } else if (temp == 48) {
        $('#groupByIntervalRange').attr('min', '1');
        $('#groupByIntervalRange').attr('max', '4');
        $('#groupByIntervalRange').attr('value', '1');
    } else if (temp == 168) {
        $('#groupByIntervalRange').attr('min', '2');
        $('#groupByIntervalRange').attr('max', '4');
        $('#groupByIntervalRange').attr('value', '2');
    } else if (temp == 672) {
        $('#groupByIntervalRange').attr('min', '2');
        $('#groupByIntervalRange').attr('max', '6');
        $('#groupByIntervalRange').attr('value', '2');
    }

    $("#viewSinceButton").text($(event.target).text());
    active_since = parseInt(temp) * 3600;
    update(active_device_id, active_since, interval_by);
});

$('#groupByIntervalRange').change(function (event) {
    var temp = $(event.target).val();
    switch (temp) {
        case "0":
            $('#groupByInterval').text("Group By Default");
            $('#groupByIntervalLabel').text("Group By Default");
            interval_by = 1 * 60;
            break;
        case "1":
            $('#groupByInterval').text("Group By 15 Min");
            $('#groupByIntervalLabel').text("Group By 15 Min");
            interval_by = 15 * 60;
            break;
        case "2":
            $('#groupByInterval').text("Group By 30 Min");
            $('#groupByIntervalLabel').text("Group By 30 Min");
            interval_by = 30 * 60;
            break;
        case "3":
            $('#groupByInterval').text("Group By 1 Hr");
            $('#groupByIntervalLabel').text("Group By 1 Hr");
            interval_by = 60 * 60;
            break;
        case "4":
            $('#groupByInterval').text("Group By 6 Hr");
            $('#groupByIntervalLabel').text("Group By 6 Hr");
            interval_by = 360 * 60;
            break;
        case "5":
            $('#groupByInterval').text("Group By 12 Hr");
            $('#groupByIntervalLabel').text("Group By 12 Hr");
            interval_by = 720 * 60;
            break;
        case "6":
            $('#groupByInterval').text("Group By 1 Day");
            $('#groupByIntervalLabel').text("Group By 1 Day");
            interval_by = 720 * 2 * 60;
            break;
        default:
            break;
    }
    update(active_device_id, active_since, interval_by);
})

function showArchive(by_year, by_month, by_date) {
    var appendTo = $('#archivedTable')
    var mac_addr = "";

    for (var i = 0; i < device_list.length; i++) {
        if (device_list[i].id == active_device_id) {
            mac_addr = device_list[i].mac;
        }
    }

    fetch('/showArchive?device_id=' + active_device_id + '&by_year=' + by_year + '&by_month=' + by_month + '&by_date=' + by_date).then(
        function (response) {
            response.json().then(function (data) {
                var archived_list = data["archived_dict"];

                if (by_year == -1) {
                    archived_list.forEach((value, index) => {
                        var li = $('<tr/>');
                        li.attr('id', value.t);
                        li.attr('data-toggle', 'collapse');
                        li.attr('href', '#tbody' + value.t);
                        li.attr('onclick', "showArchive(" + value.t + ", -1, -1)");

                        var td_time = $('<td/>').html(value.t).appendTo(li);
                        var td_mac = $('<td/>').html(mac_addr).appendTo(li);
                        var td_upload = $('<td/>').text(value.upload).appendTo(li);
                        var td_download = $('<td/>').text(value.download).appendTo(li);

                        li.appendTo(appendTo);
                    })
                } else if (by_month == -1) {
                    archived_list.forEach((value, index) => {
                        var li = $('<tr/>');
                        li.attr('data-toggle', 'collapse');
                        li.attr('href', '#tbody' + by_year + value.t);
                        li.addClass('collapse');
                        li.attr('id', 'tbody' + by_year);
                        li.attr('onclick', "showArchive(" + by_year + ", " + value.t + ", -1)");

                        var td_time = $('<td/>').html(value.t).appendTo(li);
                        var td_mac = $('<td/>').html(mac_addr).appendTo(li);
                        var td_upload = $('<td/>').text(value.upload).appendTo(li);
                        var td_download = $('<td/>').text(value.download).appendTo(li);

                        li.appendTo(appendTo);
                    })
                    //tbody.appendTo(appendTo);
                } else if (by_date == -1) {
                    archived_list.forEach((value, index) => {
                        var li = $('<tr/>');
                        li.attr('id', 'tbody' + by_year + by_month);
                        li.addClass('collapse');
                        var td_time = $('<td/>').html(value.t).appendTo(li);
                        var td_mac = $('<td/>').html(mac_addr).appendTo(li);
                        var td_upload = $('<td/>').text(value.upload).appendTo(li);
                        var td_download = $('<td/>').text(value.download).appendTo(li);

                        li.appendTo(appendTo);
                    })
                }
            })
        }
    );
}