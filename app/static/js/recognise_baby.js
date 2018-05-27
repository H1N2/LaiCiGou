function getBabyAttributes() {
	var s = $("#petId").val();
	var petId = s.replace(/[^0-9]/ig, "");
	console.log(petId);
	if (petId.length !== 19) {
		alert("狗蛋ID不正确");
	}
	$("#result").hide();
	$.ajax({
		url: "getBabyAttributes",
		type: "POST",
		dataType: 'json',
		data: {
			petId: petId
		},
		async: true,
		success: function (data) {
			setAttributes(data);
			console.log(data);
		},
		error: function () {
			alert("获取狗蛋信息失败");
		}
	});
}

function setAttributes(data) {
	$('#petUrl').attr("src", data.petUrl);
	var i = 0;
	var trs = '';
	var tds = '';
	for (var key in data) {
		if (key !== "petUrl") {
			var value = data[key].split(' ')[0];
			var rare = "<font color=\"red\">" + data[key].split(' ')[1] + "</font>";
			td = '<td>' + key + '： ' + value + " " + rare + "</td>";
			tds = tds + td;
			i = i + 1;
			if (i % 2 == 0) {
				trs = trs + '<tr>' + tds + '</tr>';
				tds = '';
			}
		}
	}
	var tbody = '<tbody><tr><td><h3 class="text-left">属性</h3></td><td></td></tr>' + trs + '</tbody>';
	$("#attributesTable").html(tbody);
	$("#result").show();
}

$("#result").hide();
