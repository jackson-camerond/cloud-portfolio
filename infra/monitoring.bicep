// monitoring.bicep — uptime monitoring for the portfolio site (camdjackson.com).
//
// Pings the PUBLIC url every 5 min from 5 US regions and checks:
//   - HTTP 200
//   - valid SSL (warns if cert < 7 days from expiry)
//   - the page actually contains "Cameron Jackson"  (catches "200 but wrong content")
// Emails an alert when >= 2 regions fail (avoids single-region flakiness).
// Monitoring the public URL covers the whole chain end-to-end: Cloudflare -> Worker -> Azure.
//
// Deploy:
//   az deployment group create -g rg-cloud-portfolio \
//     --template-file infra/monitoring.bicep \
//     --parameters alertEmail=you@example.com

@description('Email that receives down alerts.')
param alertEmail string

@description('Public URL to monitor (end-to-end).')
param siteUrl string = 'https://camdjackson.com/'

@description('Text that must be present on the page (guards against 200-but-broken).')
param contentMatch string = 'Cameron Jackson'

param location string = resourceGroup().location

var aiName = 'ai-camdjackson'
var testName = 'avail-camdjackson'

resource ai 'Microsoft.Insights/components@2020-02-02' = {
  name: aiName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
  }
}

resource webtest 'Microsoft.Insights/webtests@2022-06-15' = {
  name: testName
  location: location
  tags: {
    'hidden-link:${ai.id}': 'Resource'
  }
  kind: 'standard'
  properties: {
    SyntheticMonitorId: testName
    Name: 'camdjackson.com availability'
    Enabled: true
    Frequency: 300
    Timeout: 30
    Kind: 'standard'
    RetryEnabled: true
    Locations: [
      { Id: 'us-ca-sjc-azr' }
      { Id: 'us-tx-sn1-azr' }
      { Id: 'us-il-ch1-azr' }
      { Id: 'us-va-ash-azr' }
      { Id: 'us-fl-mia-edge' }
    ]
    Request: {
      RequestUrl: siteUrl
      HttpVerb: 'GET'
      ParseDependentRequests: false
    }
    ValidationRules: {
      ExpectedHttpStatusCode: 200
      SSLCheck: true
      SSLCertRemainingLifetimeCheck: 7
      ContentValidation: {
        ContentMatch: contentMatch
        IgnoreCase: true
        PassIfTextFound: true
      }
    }
  }
}

resource ag 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: 'ag-camdjackson-down'
  location: 'global'
  properties: {
    groupShortName: 'sitedown'
    enabled: true
    emailReceivers: [
      {
        name: 'owner'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ]
  }
}

resource alert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alert-camdjackson-down'
  location: 'global'
  properties: {
    description: 'camdjackson.com is failing its availability test'
    severity: 1
    enabled: true
    scopes: [
      webtest.id
      ai.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.WebtestLocationAvailabilityCriteria'
      webTestId: webtest.id
      componentId: ai.id
      failedLocationCount: 2
    }
    actions: [
      {
        actionGroupId: ag.id
      }
    ]
  }
}
