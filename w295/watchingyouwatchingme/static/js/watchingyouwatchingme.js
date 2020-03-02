﻿var WYWMApp = angular.module('WYWMApp', []);

WYWMApp.controller('WYWMController', ['$scope','$http', '$timeout', '$filter', function ($scope, $http, $timeout, $filter) {

  $scope.userprofileimage = 'static/img/noprofileimg.jpg';
  $scope.loggedin = false;

  $http.get('/userinfo').then(function(response) {
    if (response.data == "")
      return;

    $scope.userinfo = response.data;
    $scope.userprofileimage = $scope.userinfo.profile_image_url_https;
    $scope.loggedin = true;
    $scope.alltweets = true;
    $scope.allfriends = false;
    $scope.alllikes = false;
    $scope.republcan_score = 0.0;
    $scope.democrat_score = 0.0;

    $http.get('/usertweets').then(function(response) {
      $scope.usertweets = response.data;
      $scope.usertweets.forEach(function (tweet) {
        if (tweet.is_political)
        {
          score = tweet.mnb_sentiment * tweet.pt * tweet.pr;
          if (score > 0)
          {
            $scope.republcan_score += score;
          }
          else
          {
            $scope.democrat_score += -score;
          }
        }
      });
    });

    $http.get('/userfriends').then(function(response) {
      $scope.userfriends = response.data;
      $scope.userfriends.forEach(function (friend) {
        score = friend.pt * friend.pr;
        if (score > 0)
        {
          $scope.republcan_score += score;
        }
        else if (score < 0)
        {
          $scope.democrat_score += -score;
        }
      });
    });

    $http.get('/userlikes').then(function(response) {
      $scope.userlikes = response.data;
      $scope.userlikes.forEach(function (like) {
        score = like.pt * like.pr;
        if (score > 0)
        {
          $scope.republcan_score += score;
        }
        else if (score < 0)
        {
          $scope.democrat_score += -score;
        }
      });
    });
  });
}]);
