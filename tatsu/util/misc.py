# flake8: noqa
# pylint: skip-file
from __future__ import annotations


def check_pickle(xThing, lTested = None):
    # https://stackoverflow.com/a/50049341/545637

    # FIXME: clean up an use exceptions

    import pickle
    lTested = [] if lTested is None else lTested
    if id(xThing) in lTested:
        return lTested
    sType = type(xThing).__name__
    print('Testing {0}...'.format(sType))

    if sType in ['type','int','str', 'bool', 'NoneType', 'unicode']:
        print('...too easy')
        return lTested
    if sType == 'dict':
        print('...testing members')
        for k in xThing:
            lTested = check_pickle(xThing[k], lTested)
        print('...tested members')
        return lTested
    if sType == 'list':
        print('...testing members')
        for x in xThing:
            lTested = check_pickle(x)
        print('...tested members')
        return lTested

    lTested.append(id(xThing))
    oClass = type(xThing)

    for s in dir(xThing):
        if s.startswith('_'):
            print('...skipping *private* thingy')
            continue
        #if it is an attribute: Skip it
        try:
            xClassAttribute = oClass.__getattribute__(oClass,s)
        except (AttributeError, TypeError):
            pass
        else:
            if type(xClassAttribute).__name__ == 'property':
                print('...skipping property')
                continue

        xAttribute = xThing.__getattribute__(s)
        print('Testing {0}.{1} of type {2}'.format(sType,s,type(xAttribute).__name__))
        if type(xAttribute).__name__ == 'function':
            print("...skipping function")
            continue
        if type(xAttribute).__name__ in ['method', 'instancemethod']:
            print('...skipping method')
            continue
        if type(xAttribute).__name__ == 'HtmlElement':
            continue
        if type(xAttribute) == dict:
            print('...testing dict values for {0}.{1}'.format(sType,s))
            for k in xAttribute:
                lTested = check_pickle(xAttribute[k])
                continue
            print('...finished testing dict values for {0}.{1}'.format(sType,s))

        try:
            oIter = xAttribute.__iter__()
        except (AttributeError, TypeError):
            pass
        except AssertionError:
            pass #lxml elements do this
        else:
            print('...testing iter values for {0}.{1} of type {2}'.format(sType,s,type(xAttribute).__name__))
            for x in xAttribute:
                lTested = check_pickle(x, lTested)
            print('...finished testing iter values for {0}.{1}'.format(sType,s))

        try:
            xAttribute.__dict__
        except AttributeError:
            pass
        else:
            #this attribute should be explored seperately...
            lTested = check_pickle(xAttribute, lTested)
            continue
        print(0, xThing, xAttribute)
        pickle.dumps(xAttribute)

    print('Testing {0} as complete object'.format(sType))
    pickle.dumps(xThing)
    return lTested
