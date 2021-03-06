function getAssetData() {
	$.ajax({
		url: "getAssetData",
		type: "POST",
		dataType: 'json',
		data: {},
		async: true,
		success: function (data) {
			drawLines(data);
			console.log(data);
		},
		error: function () {
			alert("getAssetData error");
		}
	});
}

function drawLines(asset) {
	// 基于准备好的dom，初始化echarts实例
	var myChart = echarts.init(document.getElementById('asset_trend'));
	option = {
		title: {
			text: '微积分财富趋势图'
		},
		tooltip: {
			trigger: 'axis'
		},
		legend: {
			data: ['收入', '支出', '总数']
		},
		grid: {
			left: '3%',
			right: '4%',
			bottom: '3%',
			containLabel: true
		},
		//		toolbox: {
		//			feature: {
		//				saveAsImage: {}
		//			}
		//		},
		xAxis: {
			type: 'category',
			boundaryGap: false,
			data: asset['dates']
		},
		yAxis: {
			type: 'value'
		},
		series: [{
				name: '收入',
				type: 'line',
				data: asset['incomes']
			}, {
				name: '支出',
				type: 'line',
				data: asset['expends']
			}, {
				name: '总数',
				type: 'line',
				data: asset['totals']
			}
		]
	};

	// 使用刚指定的配置项和数据显示图表。
	myChart.setOption(option);
	window.onresize = myChart.resize;
	// 使用刚指定的配置项和数据显示图表。
	myChart.setOption(option);
}

getAssetData();
