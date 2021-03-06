#ifndef COUPLINGDATAREADER_H
#define COUPLINGDATAREADER_H

#include "../CouplingDataUser.h"

namespace adapter
{

class CouplingDataReader : public CouplingDataUser
{

protected:

public:

	virtual void read( double * dataBuffer ) = 0;
	virtual ~CouplingDataReader()
	{
	}

};

}

#endif // COUPLINGDATAREADER_H
