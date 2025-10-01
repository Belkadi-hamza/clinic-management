$(function() {
	'use strict';

  	Chart.defaults.borderColor = "#ced2d4";

	if ($('#chartBar1').length > 0) {
	var ctx1 = document.getElementById('chartBar1').getContext('2d');
	new Chart(ctx1, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
			datasets: [{
				label: 'Sales',
				data: [24, 10, 32, 24, 26, 20],
				backgroundColor: '#1F6DB2'
			}]
		},
		options: {
			maintainAspectRatio: false,
			responsive: true,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				x: { 
					ticks: {
					  font: { size: 11 }, 
					  beginAtZero: true
					},
				  },
				  y: {
					ticks: {
					  font: { size: 10 }, 
					  beginAtZero: true,
					  max: 80
					}
				},
			}
		}
	});
}
if ($('#chartBar2').length > 0) {
	var ctx2 = document.getElementById('chartBar2').getContext('2d');
	new Chart(ctx2, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
			datasets: [{
				label: 'Sales',
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor: '#c6daeb'
			}]
		},
		options: {
			maintainAspectRatio: false,
			responsive: true,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				x: {
				  ticks: {
					beginAtZero: true,
					font: { size: 11 } // ✅ Correct way to set font size in v4
				  },
				  barPercentage: 0.6 // ✅ Moved outside `ticks`
				},
				y: {
				  ticks: {
					beginAtZero: true,
					font: { size: 10 }, // ✅ Correct font size format
					max: 80 // ✅ Sets max value for the Y-axis
				  }
				}
			}
		}
	});
}
if ($('#chartBar3').length > 0) {
	var ctx3 = document.getElementById('chartBar3').getContext('2d');
	var gradient = ctx3.createLinearGradient(0, 0, 0, 250);
	gradient.addColorStop(0, '#0d7858');
	gradient.addColorStop(1, '#1f6db2');
	new Chart(ctx3, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
			datasets: [{
				label: 'Sales',
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor: gradient
			}]
		},
		options: {
			maintainAspectRatio: false,
			responsive: true,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				x: {
				  ticks: {
					beginAtZero: true,
					font: { size: 11 } 
				  },
				  barPercentage: 0.6 
				},
				y: {
				  ticks: {
					beginAtZero: true,
					font: { size: 10 }, 
					max: 80 
				  }
				}
			  }
		}
	});
}
if ($('#chartBar4').length > 0) {

	var ctx4 = document.getElementById('chartBar4').getContext('2d');
	new Chart(ctx4, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
			datasets: [{
				label: 'Sales',
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor: ['#1F6DB2', '#1976D2', '#09800F', '#303F9F', '#FDAF22', '#09800F']
			}]
		},
		options: {
			indexAxis: 'y',
			maintainAspectRatio: false,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				x: {
				  ticks: {
					beginAtZero: true,
					font: { size: 11 } 
				  }
				},
				y: {
				  ticks: {
					beginAtZero: true,
					font: { size: 10 }, 
					max: 80 
				  }
				}
			  }
		}
	});
}
if ($('#chartBar5').length > 0) {
	var ctx5 = document.getElementById('chartBar5').getContext('2d');
	new Chart(ctx5, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
			datasets: [{
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor: [ '#1F6DB2', '#1976D2', '#09800F', '#FDAF22', '#B71C1C']
			}, {
				data: [22, 30, 25, 30, 20, 40],
				backgroundColor: '#44c4fa'
			}]
		},
		options: {
			indexAxis: 'y',
			maintainAspectRatio: false,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				y: {
					ticks: {
						beginAtZero: true,
						font: { size: 11 } 
					}
				},
				x: {
					ticks: {
						beginAtZero: true,
						font: { size: 11 }, 
						max: 80
					}
				}
			}
		}
	});
}
	/** STACKED BAR CHART **/
if ($('#chartStacked1').length > 0) {
	var ctx6 = document.getElementById('chartStacked1');
	new Chart(ctx6, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
			datasets: [{
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor: '#1F6DB2',
				borderWidth: 1,
				fill: true
			}, {
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor:  '#0D7858',
				borderWidth: 1,
				fill: true
			}]
		},
		options: {
			maintainAspectRatio: false,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				y: {
					stacked: true,
					ticks: {
						beginAtZero: true,
						font: { size: 11 } 
					}
				},
				x: {
					barPercentage: 0.5,
					stacked: true,
					ticks: {
						font: { size: 11 } 
					}
				}
			}
		}
	});
}
if ($('#chartStacked2').length > 0) {
	var ctx7 = document.getElementById('chartStacked2');
	new Chart(ctx7, {
		type: 'bar',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
			datasets: [{
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor: '#1F6DB2',
				borderWidth: 1,
				fill: true
			}, {
				data: [14, 12, 34, 25, 24, 20],
				backgroundColor:  '#0D7858',
				borderWidth: 1,
				fill: true
			}]
		},
		options: {
			indexAxis: 'y',
			maintainAspectRatio: false,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				y: {
					stacked: true,
					ticks: {
						beginAtZero: true,
						font: { size: 10 }, 
						max: 80
					}
				},
				x: {
					stacked: true,
					ticks: {
						beginAtZero: true,
						font: { size: 11 } 
					}
				}
			}
		}
	});
}

// Time Chart

if ($('#time-chart').length > 0) {
    var sCol = {
      chart: {
        width: '56',
        height: 70,
        type: 'bar',
        toolbar: {
          show: false,
        },
        padding: 0
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: '100%', // Removes space between bars
            barHeight: '100%',
          endingShape: 'rounded'
        },
      },
      colors: ['#7539FF', '#EFEEFF'],
      states: {
        hover: {
            filter: {
                type: 'darken', // Options: 'none', 'lighten', 'darken'
                value: 0.3 // Adjust hover intensity
            }
        }
    },
      dataLabels: {
        enabled: false
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
      },
      series: [{
        name: 'Tax Collected',
        data: [4, 6, 9, 9, 7,]
      }],
      fill: {
        opacity: 1

      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        labels: { show: false },
        axisTicks: { show: false },
        axisBorder: { show: false } 
    },
    grid: {
      show: false, // Set false to hide all grid lines
      padding: { left: 0, right: 0, top: -15, bottom: -25 } 
  },
      yaxis: {
        labels: { show: false }  // Hides Y-axis values
    },
      tooltip: {
        y: {
          formatter: function (val) {
            return  val 
          }
        }
      }
    }

    var chart = new ApexCharts(
      document.querySelector("#time-chart"),
      sCol
    );

    chart.render();
  }

  if ($('#time-chart02').length > 0) {
    var sCol = {
      chart: {
        width: '56',
        height: 70,
        type: 'bar',
        toolbar: {
          show: false,
        },
        padding: 0
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: '100%', // Removes space between bars
            barHeight: '100%',
          endingShape: 'rounded'
        },
      },
	  colors: ['#27AE60', '#EFEEFF'],
      states: {
        hover: {
            filter: {
                type: 'darken', // Options: 'none', 'lighten', 'darken'
                value: 0.3 // Adjust hover intensity
            }
        }
    },
      dataLabels: {
        enabled: false
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
      },
      series: [{
        name: 'GST',
        data: [4, 6, 9, 9, 7,]
      }],
      fill: {
        opacity: 1

      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        labels: { show: false },
        axisTicks: { show: false },
        axisBorder: { show: false } 
    },
    grid: {
      show: false, // Set false to hide all grid lines
      padding: { left: 0, right: 0, top: -15, bottom: -25 } 
  },
      yaxis: {
        labels: { show: false }  // Hides Y-axis values
    },
      tooltip: {
        y: {
          formatter: function (val) {
            return  val 
          }
        }
      }
    }

    var chart = new ApexCharts(
      document.querySelector("#time-chart02"),
      sCol
    );

    chart.render();
  }


  // Time Chart03

  if ($('#time-chart03').length > 0) {
    var sCol = {
      chart: {
        width: '56',
        height: 70,
        type: 'bar',
        toolbar: {
          show: false,
        },
        padding: 0
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: '100%', // Removes space between bars
            barHeight: '100%',
          endingShape: 'rounded'
        },
      },
      colors: ['#E2B93B', '#EFEEFF'],
      states: {
        hover: {
            filter: {
                type: 'darken', // Options: 'none', 'lighten', 'darken'
                value: 0.3 // Adjust hover intensity
            }
        }
    },
      dataLabels: {
        enabled: false
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
      },
      series: [{
        name: 'VAT',
        data: [4, 6, 9, 9, 7,]
      }],
      fill: {
        opacity: 1

      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        labels: { show: false },
        axisTicks: { show: false },
        axisBorder: { show: false } 
    },
    grid: {
      show: false, // Set false to hide all grid lines
      padding: { left: 0, right: 0, top: -15, bottom: -25 } 
  },
      yaxis: {
        labels: { show: false }  // Hides Y-axis values
    },
      tooltip: {
        y: {
          formatter: function (val) {
            return  val 
          }
        }
      }
    }

    var chart = new ApexCharts(
      document.querySelector("#time-chart03"),
      sCol
    );

    chart.render();
  }

  // Time Chart04

  if ($('#time-chart04').length > 0) {
    var sCol = {
      chart: {
        width: '56',
        height: 70,
        type: 'bar',
        toolbar: {
          show: false,
        },
        padding: 0
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: '100%', // Removes space between bars
            barHeight: '100%',
          endingShape: 'rounded'
        },
      },
      colors: ['#EF1E1E', '#EEEEEE'],
      states: {
        hover: {
            filter: {
                type: 'darken', // Options: 'none', 'lighten', 'darken'
                value: 0.3 // Adjust hover intensity
            }
        }
    },
      dataLabels: {
        enabled: false
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
      },
      series: [{
        name: 'Other Taxes',
        data: [4, 6, 9, 9, 7,]
      }],
      fill: {
        opacity: 1

      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        labels: { show: false },
        axisTicks: { show: false },
        axisBorder: { show: false } 
    },
    grid: {
      show: false, // Set false to hide all grid lines
      padding: { left: 0, right: 0, top: -15, bottom: -25 } 
  },
      yaxis: {
        labels: { show: false }  // Hides Y-axis values
    },
      tooltip: {
        y: {
          formatter: function (val) {
            return  val 
          }
        }
      }
    }

    var chart = new ApexCharts(
      document.querySelector("#time-chart04"),
      sCol
    );

    chart.render();
  }
  
	/* LINE CHART */
if ($('#chartLine1').length > 0) {
	var ctx8 = document.getElementById('chartLine1');
	new Chart(ctx8, {
		type: 'line',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
			datasets: [{
				data: [14, 12, 34, 25, 44, 36, 35, 25, 30, 32, 20, 25 ],
				borderColor: '#1F6DB2',
				borderWidth: 1,
				fill: false
			}, {
				data: [35, 30, 45, 35, 55, 40, 10, 20, 25, 55, 50, 45],
				borderColor: '#0D7858',
				borderWidth: 1,
				fill: false
			}]
		},
		options: {
			maintainAspectRatio: false,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				yAxeys: {
					ticks: {
						beginAtZero: true,
						font: { size: 10 }, 
						max: 80
					}
				},
				y: {
					ticks: {
						beginAtZero: true,
						font: { size: 11 } 
					}
				}
			}
		}
	});
}
	/** AREA CHART **/
if ($('#chartArea1').length > 0) {
	var ctx9 = document.getElementById('chartArea1');
	ctx9.height = 220;

	var gradient1 = ctx3.createLinearGradient(0, 350, 0, 0);
	gradient1.addColorStop(0, 'rgba(102, 77, 201,0)');
	gradient1.addColorStop(1, 'rgba(102, 77, 201,.5)');
	var gradient2 = ctx3.createLinearGradient(0, 280, 0, 0);
	gradient2.addColorStop(0, 'rgba(91, 115, 232,0)');
	gradient2.addColorStop(1, 'rgba(91, 115, 232,.5)');
	new Chart(ctx9, {
		type: 'line',
		data: {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
			datasets: [{
				data: [14, 12, 34, 25, 44, 36, 35, 25, 30, 32, 20, 25 ],
				borderColor: '#1F6DB2',
				borderWidth: 1,
				backgroundColor: gradient1
			}, {
				data: [35, 30, 45, 35, 55, 40, 10, 20, 25, 65, 50, 45],
				borderColor: '#0D7858',
				borderWidth: 1,
				backgroundColor: gradient2
			}]
		},
		options: {
			maintainAspectRatio: false,
			legend: {
				display: false,
				labels: {
					display: false
				}
			},
			scales: {
				y: {
					ticks: {
						beginAtZero: true,
						font: { size: 10 }, 
						max: 100
					}
				},
				x: {
					ticks: {
						beginAtZero: true,
						font: { size: 11 } 
					}
				}
			}
		}
	});

	/** PIE CHART **/
	var datapie = {
		labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
		datasets: [{
			data: [35,20,8,15,24],
			backgroundColor: ['#664dc9', '#44c4fa', '#38cb89', '#3e80eb', '#ffab00', '#ef4b4b']
		}]
	};
	var optionpie = {
		maintainAspectRatio: false,
		responsive: true,
		legend: {
			display: false,
		},
		animation: {
			animateScale: true,
			animateRotate: true
		}
	};
}
	// For a doughnut chart
if ($('#chartPie').length > 0) {
	var ctx6 = document.getElementById('chartPie');
	var myPieChart6 = new Chart(ctx6, {
		type: 'doughnut',
		data: datapie,
		options: optionpie
	});
	/** PIE CHART **/
	var datapie = {
		labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
		datasets: [{
			data: [35,20,8,15,24],
			backgroundColor: ['#1F6DB2', '#1976D2', '#6A1B9A', '#303F9F', '#FDAF22', '#09800F']
		}]
	};
	var optionpie = {
		maintainAspectRatio: false,
		responsive: true,
		legend: {
			display: false,
		},
		animation: {
			animateScale: true,
			animateRotate: true
		}
	};
}
	// For a pie chart
if ($('#chartDonut').length > 0) {
	var ctx7 = document.getElementById('chartDonut');
	var myPieChart7 = new Chart(ctx7, {
		type: 'pie',
		data: datapie,
		options: optionpie
	});
	/** PIE CHART **/
	var datapie = {
		labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
		datasets: [{
			data: [35,20,8,15,24],
			backgroundColor: ['#1F6DB2', '#1976D2', '#6A1B9A', '#303F9F', '#FDAF22', '#09800F']
		}]
	};
	var optionpie = {
		maintainAspectRatio: false,
		responsive: true,
		legend: {
			display: false,
		},
		animation: {
			animateScale: true,
			animateRotate: true
		}
	};

	const data = {
		datasets: [{
			label: 'Appointment',
			data: [{
			  x: -10,
			  y: 0
			}, {
			  x: 0,
			  y: 10
			}, {
			  x: 10,
			  y: 5
			}, {
			  x: 0.5,
			  y: 5.5
			}],
			backgroundColor: '#1F9CC6'
		  }],
	  };
	  
	var ctx12 = document.getElementById('chartRadar');
	var radar = new Chart(ctx12, {
		type: 'scatter',
		data: data,
		options: {
			scales: {
			x: {
				type: 'linear',
				position: 'bottom'
			}
			}
		}
	  });
	}

	if($('#mySemiDonutChart').length > 0) {
		var ctx = document.getElementById('mySemiDonutChart').getContext('2d');
    var mySemiDonutChart = new Chart(ctx, {
        type: 'doughnut', // Chart type
        data: {
            labels: ['Ongoing','Onhold', 'Completed', 'Overdue'],
            datasets: [{
                label: 'Semi Donut',
                data: [20, 40, 20, 10],
                backgroundColor: ['#FFC107', '#1B84FF', '#1F6DB2', '#0D7858'],
                borderWidth: -10,
                borderColor: 'transparent', // Border between segments
                hoverBorderWidth: 0,   // Border radius for curved edges
                cutout: '75%',   
				spacing: -30,
            }]
        },
		options: {
			rotation: -100,
			circumference: 185,
			layout: {
				padding: {
					top: -20,    // Set to 0 to remove top padding
					bottom: 20, // Set to 0 to remove bottom padding
				}
			},
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					display: false // Hide the legend
				}
			},elements: {
				arc: {
					borderWidth: -30, // Ensure consistent overlap
					borderRadius: 30, // Add some rounding
				  }
			  },
		  }
    });
	}

	if($('#tasks').length > 0) {
		var ctx = document.getElementById('tasks').getContext('2d');
    var mySemiDonutChart = new Chart(ctx, {
        type: 'doughnut', // Chart type
        data: {
            labels: ['Ongoing','Completed', 'Overdue', 'On Hold '],
            datasets: [{
                label: 'Tasks',
                data: [20, 40, 20, 20],
                backgroundColor: ['#FE9738', '#8000FF', '#01B664', '#FF0000'],
                borderWidth: 10,
				borderRadius: 0,
                borderColor: '#F3F4F6', // Border between segments
                hoverBorderWidth: 0,   // Border radius for curved edges
                cutout: '80%', 
				spacing: -25,
            }]
        },
		options: {
			rotation: -100,
			circumference: 200,
			layout: {
				padding: {
					top: 0,    // Remove top padding
                    bottom: 0, // Remove bottom padding
                    left: 0,   // Remove left padding
                    right: 0   // Remove right padding
				}
			},
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					display: false // Hide the legend
				}
			},
		  }
    });
	}

	if ($('#deal_chart').length > 0) {
		
		var ctx = document.getElementById('deal_chart').getContext('2d');
var myRadarChart = new Chart(ctx, {
    type: 'radar',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Ayg'], // Common labels for both series
        datasets: [
            {
                label: 'Email', // First series
                data: [40, 70, 20, 40, 40, 70, 40, 60],
                backgroundColor: '#2dcb73',
                borderColor: '#2dcb73',
                pointBackgroundColor: '#2dcb73',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(255, 99, 132, 1)', 
				tension: 0.3,
            },
            {
                label: 'Chat', // Second series
                data: [30, 30, 90, 30, 60, 30, 60, 90],
                backgroundColor: '#4b3088',
                borderColor: '#4b3088',
                pointBackgroundColor: '#4b3088',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
				tension: 0.4,
            },
            {
                label: 'Series 3', // Second series
                data: [70, 43, 70, 90, 30, 30, 30, 40],
                backgroundColor: '#F26522',
                borderColor: '#F26522',
                pointBackgroundColor: '#F26522',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
				tension: 0.4,
            }
        ]
    },
    options: {
		responsive: false,
        scales: {
            r: {
                angleLines: {
                    display: true,
                    color: '#e9e9e9' // Color of the radial lines
                },
                grid: {
                    circular: true // Make the grid lines circular
                },
                suggestedMin: 0,
                suggestedMax: 100,
				ticks: {
					stepSize: 30
				}
            }
        },
		plugins: {
			legend: {
				display: false // This hides the legend
			}
		}
    }
});
		
	}

});

	if ($('#activities').length > 0) {

		var ctx4 = document.getElementById('activities').getContext('2d');
		new Chart(ctx4, {
			type: 'bar',
			data: {
				labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
				datasets: [{
					data: [30, 25, 10, 20, 15, 5],
					backgroundColor: ['#3550DC', '#FE9738', '#AB47BC', '#0080FF', '#27EAEA', '#CED2D4'],
					borderRadius: 5,
				}]
			},
			options: {
				indexAxis: 'y',
				maintainAspectRatio: false,
				legend: {
					display: false,
					labels: {
						display: false
					}
				},
				scales: {
					yAxes: [{
						ticks: {
							beginAtZero: true,
							fontSize: 10,
						}
					}],
					xAxes: [{
						ticks: {
							beginAtZero: true,
							fontSize: 11,
							max: 80
						}
					}]
				}
			}
		});
	}



	if ($('#attendance').length > 0) {
		var ctx1 = document.getElementById('attendance').getContext('2d');
	
		// Plugin to draw center text BEFORE tooltips
		const centerTextPlugin = {
			id: 'centerText',
			beforeDraw(chart) { // <-- changed from afterDraw to beforeDraw
				const { width, height } = chart;
				const ctx = chart.ctx;
				ctx.save();
	
				// Subtitle
				ctx.font = '16px Arial';
				ctx.fillStyle = '#666';
				ctx.textAlign = 'center';
				ctx.textBaseline = 'middle';
	
				// Big number
				ctx.font = 'bold 28px Arial';
				ctx.fillStyle = '#000';
	
				ctx.restore();
			}
		};

		// External HTML tooltip to ensure it renders above any DOM overlays
		const externalTooltipHandler = (context) => {
			const { chart, tooltip } = context;
			let tooltipEl = chart._externalTooltipEl;

			// Ensure curved tooltip styling exists (rounded box + caret)
			if (!document.getElementById('chartjs-tooltip-style')) {
				const style = document.createElement('style');
				style.id = 'chartjs-tooltip-style';
				style.textContent = `
.chartjs-tooltip{ border-radius:12px; box-shadow:0 8px 24px rgba(0,0,0,.25); }
.chartjs-tooltip::after{ content:''; position:absolute; left:50%; transform:translateX(-50%) rotate(45deg); width:5px; height:5px; bottom:-6px; background:var(--chartjs-tooltip-bg, #222); border-left:1px solid var(--chartjs-tooltip-border, #fff); border-top:1px solid var(--chartjs-tooltip-border, #fff); border-radius:2px; }
`;
				document.head.appendChild(style);
			}

			if (!tooltipEl) {
				tooltipEl = document.createElement('div');
				tooltipEl.className = 'chartjs-tooltip';
				tooltipEl.style.position = 'absolute';
				tooltipEl.style.pointerEvents = 'none';
				tooltipEl.style.background = '#222';
				tooltipEl.style.color = '#fff';
				tooltipEl.style.border = '1px solid #fff';
				tooltipEl.style.borderRadius = '12px';
				tooltipEl.style.padding = '10px 12px';
				tooltipEl.style.font = '14px Arial';
				tooltipEl.style.transition = 'all .08s ease';
				tooltipEl.style.zIndex = '9999';
				// Variables used by the caret pseudo-element
				tooltipEl.style.setProperty('--chartjs-tooltip-bg', '#222');
				tooltipEl.style.setProperty('--chartjs-tooltip-border', '#fff');
				document.body.appendChild(tooltipEl);
				chart._externalTooltipEl = tooltipEl;
			}

			// Hide when not visible
			if (tooltip.opacity === 0) {
				tooltipEl.style.opacity = 0;
				return;
			}

			// Set text
			if (tooltip.body) {
				const titleLines = tooltip.title || [];
				const bodyLines = tooltip.body.map(b => b.lines);

				let innerHtml = '';
				if (titleLines.length) {
					innerHtml += '<div style="font-weight:600;margin-bottom:4px;">' + titleLines.join('<br/>') + '</div>';
				}
				innerHtml += '<div>' + bodyLines.join('<br/>') + '</div>';
				tooltipEl.innerHTML = innerHtml;
			}

			// Positioning
			const canvasRect = chart.canvas.getBoundingClientRect();
			tooltipEl.style.opacity = 1;
			tooltipEl.style.left = (window.pageXOffset + canvasRect.left + tooltip.caretX + 12) + 'px';
			tooltipEl.style.top = (window.pageYOffset + canvasRect.top + tooltip.caretY + 12) + 'px';
		};
	
		var mySemiDonutChart = new Chart(ctx1, {
			type: 'doughnut',
			data: {
				labels: [
					'Cardiology', 'Neurology', 'Neurology',
					'Dermatology', 'Orthopedics', 'Urology', 'Radiology'
				],
				datasets: [{
					data: [20, 15, 15, 10, 20, 20, 10],
					backgroundColor: [
						'#3189A1', '#7736A4', '#EB642F',
						'#FEB746', '#3F51A9', '#3683D7', '#FF5C8D'
					],
					borderWidth: 1,
					borderRadius: 10,
					borderColor: '#fff',
					hoverBorderWidth: 1,
					cutout: '85%'
				}]
			},
			options: {
				layout: {
					padding: {
						top: -20,
						bottom: -20
					}
				},
				interaction: {
					mode: 'nearest',
					intersect: false
				},
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: false
					},
					tooltip: {
						enabled: false,
						external: externalTooltipHandler
					}
				}
			},
			plugins: [centerTextPlugin]
		});
	}
	
	
	
	
	
	