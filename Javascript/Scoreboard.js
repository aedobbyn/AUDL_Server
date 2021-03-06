getScoreboard = function( data ) {
	var parsedData = jQuery.parseJSON(data)
	var home_img = new Image();
	home_img.src = "http://52.7.194.101:4002/Logos/TeamIcons_" + parsedData["hteam"] + ".png";
	var away_img = new Image();
	away_img.src = "http://52.7.194.101:4002/Logos/TeamIcons_" + parsedData["ateam"] + ".png";
	
	var table = "";
	table += "<table>";
	table += "<tr>";
	table += "<th class=status colspan='2'>" + parsedData["status"];
	table += "</th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th><th>T</th></tr>";
	table += "<tr>"
	table += "<td><img src='http://52.7.194.101:4002/Logos/TeamIcons_" + parsedData["hteam"] + ".png'></td>";
	table += "<td>" + parsedData["hteam"]  + "</td>";
	table += "<td>0</td><td>0</td><td>0</td><td>0</td>";
	table += "<td>" + parsedData["home_score"]  + "</td>";
	table += "</tr><tr>"
	table += "<td><img src='http://52.7.194.101:4002/Logos/TeamIcons_" + parsedData["ateam"] + ".png'></td>";
	table += "<td>" + parsedData["ateam"]  + "</td>";
	table += "<td>0</td><td>0</td><td>0</td><td>0</td>";
	table += "<td>" + parsedData["away_score"]  + "</td>";
	table += "</tr>";
	table += "</table>";
	$( window ).load(function() { 
		$(".scoreboard").append(table);
	});
};

scoreboard = function( teamID ) 
{
	$(document).ready(function() {
		$.ajax({
			url: "http://52.7.194.101:4002/Web/Score",
			jsonp: "callback",
			dataType : "jsonp",
			jsonpCallback : "getScoreboard",
			data : {"id" : teamID}
		});
	});
};
