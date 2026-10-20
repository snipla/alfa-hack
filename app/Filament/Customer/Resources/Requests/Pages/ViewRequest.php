<?php

namespace App\Filament\Customer\Resources\Requests\Pages;

use App\Filament\Customer\Resources\Requests\RequestResource;
use Filament\Actions\EditAction;
use Filament\Resources\Pages\ViewRecord;

class ViewRequest extends ViewRecord
{
    protected static string $resource = RequestResource::class;

    protected function getHeaderActions(): array
    {
        return [
            EditAction::make(),
        ];
    }
}
