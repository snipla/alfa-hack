<?php

namespace App\Filament\Customer\Resources\Requests\Schemas;

use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Textarea;
use Filament\Schemas\Schema;

class RequestForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('user_id')
                    ->required()
                    ->numeric(),
                TextInput::make('status')
                    ->required()
                    ->default('created'),
                Textarea::make('credit_info')
                    ->default(null)
                    ->columnSpanFull(),
            ]);
    }
}
