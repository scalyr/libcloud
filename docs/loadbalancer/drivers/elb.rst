========================================
Elastic Load Balancing interface for AWS
========================================

This tutorial will focus on libcloud Elastic Load Balancing interface for AWS.

Refer more about ELB at AWS Site
      http://docs.aws.amazon.com/ElasticLoadBalancing/latest/APIReference/Welcome.html

Creating a Connection
---------------------

The first step in accessing ELB is to create a connection to the service.

    >>> from libcloud.loadbalancer.types import Provider, State
    >>> from libcloud.loadbalancer.providers import get_driver
    >>> driver = get_driver(Provider.ELB)
    >>> elb = driver('access key id', 'secret key id', region='')

'access key' and 'secret key' id's can be found at security credentials page of AWS management console.


Getting Existing Load Balancers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To retrieve any exiting load balancers:

    >>> elb.list_balancers()
    [<LoadBalancer: id=balancer_id, name=balancer_name, state=balancer_state>]



Creating New Load Balancers
^^^^^^^^^^^^^^^^^^^^^^^^^^^
To create new load balancer initialise some members for the load balancer:

    >>> members = (Member(None, 'IP', Port),
                   Member(None, '192.168.88.2', 8080))
    >>> new_balancer = driver.create_balancer(name=balancer_name,
                                          algorithm=Algorithm.ROUND_ROBIN,
                                          port=80,
                                          protocol='http',
                                          members=members)
    [<LoadBalancer: id=balancer_id, name=balancer_name, state=balancer_state>]

Creating Load Balancer Policy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To creates a new policy for a load balancer that contains the necessary attributes depending on the policy type

    >>> elb.ex_create_balancer_policy(name=balancer_name,
                                      policy_name='EnableProxyProtocol',
                                      policy_type='ProxyProtocolPolicyType',
                                      policy_attributes={'ProxyProtocol':'true'})
    True

To get all policy associated with the load balancer

    >>> elb.ex_list_balancer_policies(balancer_name)
    ['EnableProxyProtocol']

To get all the policy types availabe

    >>> elb.ex_list_balancer_policy_types()
    ['ProxyProtocolPolicyType']

To delete a policy associated with the load balancer

    >>> elb.ex_delete_balancer_policy(name= balancer_name,
                                      policy_name='EnableProxyProtocol'):
    True

Enable/Disable Policy on Backend server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To enable the policies on the server we need to call "SetLoadBalancerPoliciesForBackendServer" action.

    >>> elb.ex_set_balancer_policies_backend_server(name=balancer_name,
                                                    port=80,
                                                    policies=['MyDurationStickyPolicy'])
    True

To disable the policy

    >>> elb.ex_set_balancer_policies_backend_server(name=balancer_name,
                                                    port=80,
                                                    policies='')
    True

Enable/Diable Policy on Listeners
^^^^^^^^^^^^^^^^^^^^^^^^^^
To create one or more listeners on a load balancer for the specified port

    >>> elb.ex_create_balancer_listeners(name=balancer_name,
                                         listeners=[[1024, 65533, 'HTTPS', 'arn:aws:iam::123456789012:server-certificate/servercert']])
    True

As mentioned above for backend Server, to enable the policies on the listeners, need to call "SetLoadBalancerPoliciesOfListener" action

    >>> elb.ex_set_balancer_policies_listener(name=balancer_name,
                                              port=80,
                                              policies=['MyDurationStickyPolicy'])
    True

To disable the policy on the listener just remove that from the policy list when calling the method

    >>> elb.ex_set_balancer_policies_listener(name=balancer_name,
                                              port=80,
                                              policies=[''])
    True

