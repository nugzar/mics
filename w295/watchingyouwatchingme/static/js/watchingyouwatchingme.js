﻿﻿var WYWMApp = angular.module('WYWMApp', []);

WYWMApp.controller('WYWMController', ['$scope','$http', '$timeout', '$filter', function ($scope, $http, $timeout, $filter) {

  $scope.userprofileimage = 'static/img/noprofileimg.jpg';
  $scope.loggedin = false;

  $http.get('/userinfo').then(function(response) {
    if (response.data == "")
      return;

    $scope.userinfo = response.data;
    $scope.userprofileimage = $scope.userinfo.profile_image_url_https;
    $scope.loggedin = true;

    $http.get('/usertweets').then(function(response) {
      $scope.usertweets = response.data;
    });

    $http.get('/userfriends').then(function(response) {
      $scope.userfriends = response.data;
    });

  });

}]);
