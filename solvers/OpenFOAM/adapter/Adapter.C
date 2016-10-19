#include "Adapter.h"

void adapter::Adapter::_storeCheckpointTime ()
{
	_couplingIterationTimeIndex = _runTime.timeIndex();
	_couplingIterationTimeValue = _runTime.value();
}

void adapter::Adapter::_reloadCheckpointTime ()
{
	_runTime.setTime( _couplingIterationTimeValue, _couplingIterationTimeIndex );
}

adapter::Adapter::Adapter( precice::SolverInterface & precice, fvMesh & mesh, Foam::Time & runTime, std::string solverName ) :
	_precice( precice ),
	_mesh( mesh ),
	_runTime( runTime ),
	_solverName( solverName )
{
}

adapter::Interface & adapter::Adapter::addNewInterface ( std::string meshName, std::vector<std::string> patchNames )
{
	adapter::Interface * interface = new adapter::Interface( _precice, _mesh, meshName, patchNames );
	_interfaces.push_back( interface );
	return *interface;
}

void adapter::Adapter::receiveCouplingData ()
{
	for ( uint i = 0 ; i < _interfaces.size() ; i++ )
	{
		_interfaces.at( i )->receiveData();
	}
}

void adapter::Adapter::sendCouplingData ()
{
	for ( uint i = 0 ; i < _interfaces.size() ; i++ )
	{
		_interfaces.at( i )->sendData();
	}
}

void adapter::Adapter::enableCheckpointing ()
{
	_checkpointingIsEnabled = true;
}

void adapter::Adapter::addCheckpointField ( volScalarField & field )
{
	if ( _checkpointingIsEnabled )
	{
		volScalarField * copy = new volScalarField( field );
		_volScalarFields.push_back( &field );
		_volScalarFieldCopies.push_back( copy );
	}
}

void adapter::Adapter::addCheckpointField ( volVectorField & field )
{
	if ( _checkpointingIsEnabled )
	{
		volVectorField * copy = new volVectorField( field );
		_volVectorFields.push_back( &field );
		_volVectorFieldCopies.push_back( copy );
	}
}

void adapter::Adapter::addCheckpointField ( surfaceScalarField & field )
{
	if ( _checkpointingIsEnabled )
	{
		surfaceScalarField * copy = new surfaceScalarField( field );
		_surfaceScalarFields.push_back( &field );
		_surfaceScalarFieldCopies.push_back( copy );
	}
}

void adapter::Adapter::readCheckpoint ()
{
	_reloadCheckpointTime();

	for ( uint i = 0 ; i < _volScalarFields.size() ; i++ )
	{
		*( _volScalarFields.at( i ) ) = *( _volScalarFieldCopies.at( i ) );
	}

	for ( uint i = 0 ; i < _volVectorFields.size() ; i++ )
	{
		*( _volVectorFields.at( i ) ) = *( _volVectorFieldCopies.at( i ) );
	}

	for ( uint i = 0 ; i < _surfaceScalarFields.size() ; i++ )
	{
		*( _surfaceScalarFields.at( i ) ) = *( _surfaceScalarFieldCopies.at( i ) );
	}
}

void adapter::Adapter::writeCheckpoint ()
{
	_storeCheckpointTime();

	for ( uint i = 0 ; i < _volScalarFields.size() ; i++ )
	{
		*( _volScalarFieldCopies.at( i ) ) = *( _volScalarFields.at( i ) );
	}

	for ( uint i = 0 ; i < _volVectorFields.size() ; i++ )
	{
		*( _volVectorFieldCopies.at( i ) ) = *( _volVectorFields.at( i ) );
	}

	for ( uint i = 0 ; i < _surfaceScalarFields.size() ; i++ )
	{
		*( _surfaceScalarFieldCopies.at( i ) ) = *( _surfaceScalarFields.at( i ) );
	}
}

adapter::Adapter::~Adapter()
{
	for ( uint i = 0 ; i < _volScalarFieldCopies.size() ; i++ )
	{
		delete _volScalarFieldCopies.at( i );
	}

	_volScalarFieldCopies.clear();

	for ( uint i = 0 ; i < _volVectorFieldCopies.size() ; i++ )
	{
		delete _volVectorFieldCopies.at( i );
	}

	_volVectorFieldCopies.clear();

	for ( uint i = 0 ; i < _surfaceScalarFieldCopies.size() ; i++ )
	{
		delete _surfaceScalarFieldCopies.at( i );
	}

	_surfaceScalarFieldCopies.clear();

	for ( uint i = 0 ; i < _interfaces.size() ; i++ )
	{
		delete _interfaces.at( i );
	}

	_interfaces.clear();
}
