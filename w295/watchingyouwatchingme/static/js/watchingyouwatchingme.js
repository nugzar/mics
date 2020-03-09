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

    $scope.d_tweets_score = 0.0;
    $scope.d_likes_score = 0.0;
    $scope.d_friends_score = 0.0;
    $scope.r_tweets_score = 0.0;
    $scope.r_likes_score = 0.0;
    $scope.r_friends_score = 0.0;

    $http.get('/usertweets').then(function(response) {
      $scope.d_tweets_score = 0.0;
      $scope.r_tweets_score = 0.0;

      response.data.forEach(function (tweet) {
        if (tweet.is_political)
        {
          score = tweet.mnb_sentiment * tweet.pt * tweet.pr;
          if (score > 0)
          {
            $scope.republcan_score += score;
            $scope.r_tweets_score += score;
          }
          else
          {
            $scope.democrat_score += -score;
            $scope.d_tweets_score += -score;
          }
        }
      });

      $scope.usertweets = response.data;
      displayChart();
    });

    $http.get('/userfriends').then(function(response) {
      $scope.d_friends_score = 0.0;
      $scope.r_friends_score = 0.0;

      response.data.forEach(function (friend) {
        score = friend.pt * friend.pr;
        if (score > 0)
        {
          $scope.republcan_score += score;
          $scope.r_friends_score += score;
        }
        else if (score < 0)
        {
          $scope.democrat_score += -score;
          $scope.d_friends_score += -score;
        }
      });

      $scope.userfriends = response.data;
      displayChart();
    });

    $http.get('/userlikes').then(function(response) {
      $scope.d_likes_score = 0.0;
      $scope.r_likes_score = 0.0;

      response.data.forEach(function (like) {
        score = like.pt * like.pr;
        if (score > 0)
        {
          $scope.republcan_score += score;
          $scope.r_likes_score += score;
        }
        else if (score < 0)
        {
          $scope.democrat_score += -score;
          $scope.d_likes_score += -score;
        }
      });

      $scope.userlikes = response.data;
      displayChart();
    });

    function displayChart() {

      if (!$scope.usertweets || !$scope.userlikes || !$scope.userfriends)
        return;

      var ctx = document.getElementById('myChart').getContext('2d');
      var myChart = new Chart(ctx, {
          type: 'pie',
          data: {
              labels: [
                'Dem: Tweets ' + Math.round($scope.d_tweets_score / ($scope.democrat_score + $scope.republcan_score) * 100) + '%',
                'Dem: Likes ' + Math.round($scope.d_likes_score / ($scope.democrat_score + $scope.republcan_score) * 100) + '%',
                'Dem: Follows ' + Math.round($scope.d_friends_score / ($scope.democrat_score + $scope.republcan_score) * 100) + '%',
                'Rep: Tweets ' + Math.round($scope.r_tweets_score / ($scope.democrat_score + $scope.republcan_score) * 100) + '%',
                'Rep: Likes ' + Math.round($scope.r_likes_score / ($scope.democrat_score + $scope.republcan_score) * 100) + '%',
                'Rep: Follows ' + Math.round($scope.r_friends_score / ($scope.democrat_score + $scope.republcan_score) * 100) + '%'
              ],
              datasets: [{
                  data: [
                    Math.round($scope.d_tweets_score / ($scope.democrat_score + $scope.republcan_score) * 100),
                    Math.round($scope.d_likes_score / ($scope.democrat_score + $scope.republcan_score) * 100),
                    Math.round($scope.d_friends_score / ($scope.democrat_score + $scope.republcan_score) * 100),
                    Math.round($scope.r_tweets_score / ($scope.democrat_score + $scope.republcan_score) * 100),
                    Math.round($scope.r_likes_score / ($scope.democrat_score + $scope.republcan_score) * 100),
                    Math.round($scope.r_friends_score / ($scope.democrat_score + $scope.republcan_score) * 100)
                  ],
                  backgroundColor: [
                      'rgba(0, 0, 255, 1)',
                      'rgba(0, 0, 255, 0.75)',
                      'rgba(0, 0, 255, 0.5)',
                      'rgba(255, 0, 0, 1)',
                      'rgba(255, 0, 0, 0.75)',
                      'rgba(255, 0, 0, 0.5)'
                  ],
                  borderColor: [
                      'rgba(255, 255, 255, 1)',
                      'rgba(255, 255, 255, 1)',
                      'rgba(255, 255, 255, 1)',
                      'rgba(255, 255, 255, 1)',
                      'rgba(255, 255, 255, 1)',
                      'rgba(255, 255, 255, 1)'
                  ],
                  borderWidth: 1
              }]
          },
          options: {
            legend: {
              display: true,
              position: 'right'
            }
          }
      });      

    }

  });
}]);
